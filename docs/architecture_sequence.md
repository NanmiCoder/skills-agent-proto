# LangChain Skills Agent 架构时序图

本文档通过 Mermaid 时序图展示 LangChain Skills Agent 的核心架构设计。

## 1. 整体交互流程

展示用户从输入到获得响应的完整链路：

```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as CLI
    participant Agent as LangChainSkillsAgent
    participant LLM as Claude LLM
    participant Tools as Tools
    participant FS as 文件系统

    User->>CLI: 输入请求
    CLI->>Agent: stream_events(message)

    Agent->>LLM: 发送消息 + system_prompt

    loop 流式响应
        LLM-->>Agent: thinking / text / tool_call
        Agent-->>CLI: 事件流
        CLI-->>User: 实时显示
    end

    alt 需要工具调用
        LLM->>Agent: tool_call(name, args)
        Agent->>Tools: 执行工具
        Tools->>FS: 读写文件/执行命令
        FS-->>Tools: 结果
        Tools-->>Agent: tool_result
        Agent-->>LLM: 工具结果
        LLM-->>Agent: 继续响应
    end

    Agent-->>CLI: done 事件
    CLI-->>User: 最终响应
```

## 2. 三层 Skill 加载机制

Skills 的核心设计：渐进式加载，减少 token 消耗。

```mermaid
sequenceDiagram
    participant User as 用户
    participant Agent as Agent
    participant Loader as SkillLoader
    participant LLM as Claude LLM
    participant Bash as bash tool

    Note over Agent,Loader: Level 1: 启动时扫描 (~100 tokens/skill)

    Agent->>Loader: scan_skills()
    Loader->>Loader: 遍历 .claude/skills/ (项目级优先)
    Loader->>Loader: 遍历 ~/.claude/skills/ (用户级兜底)
    Loader->>Loader: 解析 SKILL.md frontmatter
    Loader-->>Agent: SkillMetadata[]
    Agent->>Agent: build_system_prompt()
    Note right of Agent: Skills 元数据<br/>注入 system_prompt

    User->>Agent: "提取这篇公众号文章"
    Agent->>LLM: 请求 + system_prompt

    Note over LLM,Loader: Level 2: 请求匹配时 (~5k tokens)

    LLM->>Agent: tool_call: load_skill("news-extractor")
    Agent->>Loader: load_skill("news-extractor")
    Loader->>Loader: 读取完整 SKILL.md
    Loader-->>Agent: SkillContent (instructions)
    Agent-->>LLM: 详细指令返回上下文

    Note over LLM,Bash: Level 3: 执行时 (仅输出进入上下文)

    LLM->>Agent: tool_call: bash("uv run .../extract.py URL")
    Agent->>Bash: 执行脚本
    Bash-->>Agent: 脚本输出 (JSON/Markdown)
    Agent-->>LLM: 仅输出，脚本代码不进入上下文
    LLM-->>User: 最终结果
```

### 设计要点

| 层级 | 触发时机 | 加载内容 | Token 消耗 |
|------|----------|----------|------------|
| Level 1 | Agent 启动 | Skills 元数据 (name + description) | ~100 tokens/skill |
| Level 2 | 请求匹配 | 完整 SKILL.md 指令 | ~5k tokens |
| Level 3 | 执行脚本 | 仅脚本输出 | 按输出大小 |

### Skills 搜索路径

Skills 从两个位置加载，**项目级优先**：

| 优先级 | 路径 | 说明 |
|--------|------|------|
| 1 (高) | `.claude/skills/` | 项目级 Skills，针对当前项目定制 |
| 2 (低) | `~/.claude/skills/` | 用户级 Skills，跨项目通用 |

当同名 Skill 同时存在于两个目录时，项目级版本会覆盖用户级版本。

## 3. 流式输出处理流程

Token 级别的实时响应机制：

```mermaid
sequenceDiagram
    participant Agent as Agent
    participant LLM as LLM
    participant Emitter as StreamEventEmitter
    participant CLI as CLI (Rich Live)
    participant User as 用户

    Agent->>LLM: stream(message, mode="messages")

    loop 每个 chunk
        LLM-->>Agent: AIMessageChunk

        alt thinking 内容
            Agent->>Emitter: thinking(content)
            Emitter-->>CLI: {type: "thinking", content}
            CLI->>CLI: 更新蓝色面板
        else text 内容
            Agent->>Emitter: text(content)
            Emitter-->>CLI: {type: "text", content}
            CLI->>CLI: 更新绿色面板
        else tool_use 块
            Agent->>Emitter: tool_call(name, args)
            Emitter-->>CLI: {type: "tool_call", name, args}
            CLI->>CLI: 显示黄色工具调用
        end

        CLI-->>User: 实时刷新显示
    end

    opt 工具执行完成
        Agent->>Emitter: tool_result(name, content)
        Emitter-->>CLI: {type: "tool_result", ...}
    end

    Agent->>Emitter: done(response)
    Emitter-->>CLI: {type: "done", response}
    CLI-->>User: 最终结果
```

### 事件类型

| 事件类型 | 描述 | CLI 显示 |
|----------|------|----------|
| `thinking` | 模型思考过程 | 蓝色面板 |
| `text` | 响应文本片段 | 绿色面板 |
| `tool_call` | 工具调用请求 | 黄色状态 + spinner |
| `tool_result` | 工具执行结果 | 格式化输出 |
| `done` | 流结束标记 | 完成状态 |
| `error` | 错误信息 | 红色提示 |

## 4. 组件职责

| 文件 | 职责 |
|------|------|
| `cli.py` | CLI 入口，Rich 流式显示，用户交互 |
| `agent.py` | LangChainSkillsAgent 核心，LangChain 集成 |
| `skill_loader.py` | Skills 扫描和加载，三层机制实现 |
| `tools.py` | 工具定义：load_skill, bash, read_file, write_file |
| `stream/emitter.py` | 流式事件格式化 |
| `stream/tracker.py` | 工具调用状态追踪 |
| `stream/formatter.py` | 工具结果格式化显示 |

## 5. 数据流向图

```mermaid
flowchart TB
    subgraph 用户层
        User[用户输入]
    end

    subgraph CLI层
        CLI[cli.py]
        Live[Rich Live Display]
    end

    subgraph Agent层
        Agent[LangChainSkillsAgent]
        Loader[SkillLoader]
        Emitter[StreamEventEmitter]
    end

    subgraph LangChain层
        LC[create_agent]
        Model[init_chat_model]
    end

    subgraph 工具层
        LoadSkill[load_skill]
        Bash[bash]
        ReadFile[read_file]
        WriteFile[write_file]
    end

    subgraph 外部资源
        FS[文件系统]
        API[Claude API]
    end

    User --> CLI
    CLI --> Agent
    Agent --> Loader
    Agent --> Emitter
    Emitter --> Live
    Live --> User

    Agent --> LC
    LC --> Model
    Model --> API

    Agent --> LoadSkill
    Agent --> Bash
    Agent --> ReadFile
    Agent --> WriteFile

    LoadSkill --> Loader
    Bash --> FS
    ReadFile --> FS
    WriteFile --> FS
```

## 关键设计理念

1. **懒加载**: Skills 按需加载，减少 token 消耗
2. **透明执行**: 脚本代码不进入上下文，只有输出进入
3. **流式优先**: 所有响应都支持 token 级流式输出
4. **大模型自主**: 让 LLM 自己阅读指令、发现脚本、决定执行
5. **项目优先**: 项目级 Skills 覆盖用户级，支持针对性定制
