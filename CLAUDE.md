# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

使用 LangChain 1.0 构建的 Skills Agent，演示 Anthropic Skills 三层加载机制的底层原理。

## 常用命令

```bash
# 安装依赖
uv sync

# 运行测试
uv run python -m pytest tests/ -v

# 运行单个测试文件
uv run python -m pytest tests/test_stream.py -v

# 运行特定测试
uv run python -m pytest tests/test_stream.py::TestToolCallTracker -v

# 交互式运行
uv run langchain-skills --interactive

# 单次执行
uv run langchain-skills "列出当前目录"

# 查看发现的 Skills
uv run langchain-skills --list-skills

# 查看 System Prompt
uv run langchain-skills --show-prompt
```

## 核心架构

### Skills 三层加载机制

| 层级 | 时机 | 实现 |
|------|------|------|
| **Level 1** | 启动时 | `SkillLoader.scan_skills()` 扫描目录，解析 YAML frontmatter，注入 system_prompt |
| **Level 2** | 请求匹配时 | `load_skill` 工具读取 SKILL.md 完整指令 |
| **Level 3** | 执行时 | `bash` 工具执行脚本，脚本代码不进入上下文 |

核心设计：让大模型成为真正的"智能体"，自己阅读指令、发现脚本、决定执行。

### 流式处理架构

```
agent.py: stream_events() → 使用 stream_mode="messages" 获取 LangChain 流式输出
    ↓
stream/tracker.py: ToolCallTracker 追踪工具调用，处理增量 JSON (input_json_delta)
    ↓
stream/emitter.py: StreamEventEmitter 生成标准化事件 (thinking/text/tool_call/tool_result/done)
    ↓
stream/formatter.py: ToolResultFormatter 格式化输出，检测 [OK]/[FAILED] 前缀
    ↓
cli.py: Rich Live Display 渲染到终端
```

### 关键流程：工具调用参数处理

LangChain 流式传输中，工具参数可能分批到达：
1. `tool_use` 块先到达（`input` 可能为 `None` 或 `{}`）
2. `input_json_delta` 分批传递参数片段
3. `finalize_all()` 在收到 `tool_result` 前解析完整 JSON

CLI 使用 `tool_id` 去重，允许同一工具调用发送多次（首次显示"执行中"，finalize 后更新完整参数）。

## 代码约定

### 工具输出格式

bash 工具使用 `[OK]`/`[FAILED]` 前缀标识执行状态：
```
[OK]

output content...

[FAILED] Exit code: 1

--- stderr ---
error message
```

### Skills 目录结构

```
.claude/skills/skill-name/
├── SKILL.md          # 必需：YAML frontmatter + 指令
├── scripts/          # 可选：可执行脚本
├── references/       # 可选：参考文档
└── assets/           # 可选：模板和资源
```

Skills 搜索路径（优先级从高到低）：
1. `.claude/skills/` (项目级)
2. `~/.claude/skills/` (用户级)

## 环境变量

| 变量 | 说明 |
|------|------|
| `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_API_KEY` | API Key |
| `ANTHROPIC_BASE_URL` | 代理地址（可选） |
| `CLAUDE_MODEL` | 模型名称，默认 `claude-sonnet-4-5-20250929` |
| `MAX_TOKENS` | 最大 tokens，默认 16000 |
