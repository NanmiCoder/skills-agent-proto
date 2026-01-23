# LangChain Skills Agent

使用 LangChain 1.0 构建的 Skills Agent，演示 Anthropic Skills 三层加载机制的底层原理。

> **B站视频**: 配合视频《Skills 原理深度解析 + Agent 实战》使用

## 特性

- **Extended Thinking**: 显示模型的思考过程（蓝色面板）
- **流式输出**: Token 级实时显示响应
- **工具调用可视化**: 显示工具名称、参数、执行结果
- **三层 Skills 加载**: Level 1 元数据注入 → Level 2 指令加载 → Level 3 脚本执行

## 快速开始

### 1. 安装

```bash
git clone https://github.com/NanmiCoder/skills-agent-proto.git
cd skills-agent-proto
uv sync
```

### 2. 配置 Claude API Key

创建 `.env` 文件：

> 使用第三方代理中转, 我推荐使用 [接口AI](https://jiekou.ai/referral?invited_code=3CF8T0)，注册绑定github得3刀试用券

```bash
ANTHROPIC_AUTH_TOKEN=sk-xxx
ANTHROPIC_BASE_URL=https://api.jiekou.ai/anthropic
```

### 3. 交互式验证

```bash
uv run langchain-skills --interactive
```

## 交互式演示

### 基础命令测试

```
You: 列出当前目录的文件
```

观察输出：
- 🔧 Tool Call: `bash` + 参数 `{"command": "ls -la"}`
- 📤 Tool Result: `[OK]` + 文件列表
- 💬 Response: AI 的总结

### Skills 加载测试

```
You: 提取这篇公众号文章 https://mp.weixin.qq.com/s/xxx
```

观察三层加载：
1. **Level 1**: Agent 在 system prompt 中看到 `news-extractor` skill 元数据
2. **Level 2**: Agent 调用 `load_skill("news-extractor")` 获取详细指令
3. **Level 3**: Agent 根据指令调用 `bash` 执行提取脚本

### 错误处理测试

```
You: 执行 exit 1
```

观察输出：
- 📤 Tool Result: `[FAILED] Exit code: 1` (红色标识)

## CLI 命令

```bash
# 交互式模式（推荐）
uv run langchain-skills --interactive

# 单次执行
uv run langchain-skills "列出当前目录"

# 禁用 Thinking（降低延迟）
uv run langchain-skills --no-thinking "执行 pwd"

# 查看发现的 Skills
uv run langchain-skills --list-skills

# 查看 System Prompt（Level 1 注入内容）
uv run langchain-skills --show-prompt
```

## 项目结构

```
skills-agent-proto/
├── src/langchain_skills/
│   ├── agent.py          # LangChain Agent (Extended Thinking)
│   ├── cli.py            # CLI 入口 (流式输出)
│   ├── tools.py          # 工具定义 (bash, load_skill, read_file, write_file)
│   ├── skill_loader.py   # Skills 发现和加载
│   └── stream/           # 流式处理模块
│       ├── emitter.py    # 事件发射器
│       ├── tracker.py    # 工具调用追踪（支持增量 JSON）
│       ├── formatter.py  # 结果格式化器
│       └── utils.py      # 常量和工具函数
├── tests/                # 单元测试 (70 tests)
│   ├── test_stream.py
│   ├── test_cli.py
│   └── test_tools.py
├── docs/                 # 文档
│   ├── skill_introduce.md
│   └── langchain_agent_skill.md
└── .claude/skills/       # 示例 Skills
    └── news-extractor/
        ├── SKILL.md
        └── scripts/extract_news.py
```

## Skills 三层加载机制

| 层级 | 时机 | Token 消耗 | 内容 |
|------|------|------------|------|
| **Level 1** | 启动时 | ~100/Skill | YAML frontmatter (name, description) |
| **Level 2** | 触发时 | <5000 | SKILL.md 完整指令 |
| **Level 3** | 执行时 | 仅输出 | 脚本执行结果（代码不进上下文） |

## 流式输出架构

```
Agent.stream_events()
    ↓
┌─────────────────────────────────────────────────────┐
│  stream/emitter.py    → 生成标准化事件              │
│  stream/tracker.py    → 追踪工具调用（处理增量JSON）│
│  stream/formatter.py  → 格式化输出（检测成功/失败） │
└─────────────────────────────────────────────────────┘
    ↓
CLI (Rich Live Display)
    ↓
┌─────────────────────────────────────────────────────┐
│  🧠 Thinking Panel (蓝色)                          │
│  🔧 Tool Call (黄色) + Args                        │
│  📤 Tool Result (绿色 ✓ / 红色 ✗)                  │
│  💬 Response Panel (绿色)                          │
└─────────────────────────────────────────────────────┘
```

## 工具输出格式

bash 工具使用 `[OK]`/`[FAILED]` 前缀标识执行状态：

```
# 成功
[OK]

file1.txt
file2.txt

# 失败
[FAILED] Exit code: 1

--- stderr ---
ls: /nonexistent: No such file or directory
```

## 运行测试

```bash
uv run python -m pytest tests/ -v
```

## 代码示例

### 作为库使用

```python
from langchain_skills import LangChainSkillsAgent

# 创建 Agent
agent = LangChainSkillsAgent(enable_thinking=True)

# 流式输出
for event in agent.stream_events("列出当前目录"):
    if event.get("type") == "tool_call":
        print(f"Tool: {event['name']}, Args: {event['args']}")
    elif event.get("type") == "tool_result":
        print(f"Result: {event['content'][:100]}")
    elif event.get("type") == "text":
        print(event["content"], end="")
```

### LangChain 1.0 API

```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

model = init_chat_model("claude-sonnet-4-5-20250929", thinking={
    "type": "enabled",
    "budget_tokens": 10000,
})

agent = create_agent(
    model=model,
    tools=[load_skill, bash, read_file, write_file],
    system_prompt=skills_prompt,
    context_schema=SkillAgentContext,
)
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` | API Key | 必填 |
| `ANTHROPIC_BASE_URL` | 代理地址 | 官方 API |
| `CLAUDE_MODEL` | 模型名称 | claude-sonnet-4-5-20250929 |
| `MAX_TOKENS` | 最大 tokens | 16000 |

## 参考文档

- [docs/skill_introduce.md](./docs/skill_introduce.md) - Skills 详细介绍
- [docs/langchain_agent_skill.md](./docs/langchain_agent_skill.md) - LangChain 实现说明

## License

MIT
