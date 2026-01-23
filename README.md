# Skills Agent

使用 Claude Agent SDK 构建的能发现和使用 Skills 的 Coding Agent。

## 核心概念

### 什么是 Skills？

Skills 是 Claude Code 的模块化能力扩展机制。每个 Skill 打包了指令、元数据和可选资源（脚本、模板），Claude 会在相关时自动使用它们。

### Skills 三层加载机制

| 层级 | 加载时机 | Token 消耗 | 内容 |
|------|----------|------------|------|
| **Level 1** | 启动时 | ~100/Skill | YAML frontmatter (name, description) |
| **Level 2** | 触发时 | <5000 | SKILL.md 主体指令 |
| **Level 3** | 按需 | 仅输出 | 脚本执行结果（代码不进上下文） |

### 核心配置

让 Agent 能使用 Skills 的关键配置：

```python
ClaudeAgentOptions(
    # 关键配置 1：启用 Skills 发现
    setting_sources=["user", "project"],
    # "user" = ~/.claude/skills/
    # "project" = .claude/skills/

    # 关键配置 2：允许使用 Skill 工具
    allowed_tools=["Skill", "Read", "Bash", ...],
)
```

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv
uv sync

# 或使用 pip
pip install -e .
```

### 2. 设置 API Key

```bash
export ANTHROPIC_API_KEY=your-api-key
```

### 3. 运行示例

```bash
# 基本使用
uv run python examples/basic_usage.py

# 文章提取（需要 news-extractor skill）
uv run python examples/extract_article.py "https://mp.weixin.qq.com/s/xxx"

# 交互式对话
uv run python examples/interactive_chat.py

# 或使用 CLI
uv run skills-agent "列出所有可用的 Skills"
uv run skills-agent --interactive
```

## 项目结构

```
skills-agent-proto/
├── src/
│   └── skills_agent/
│       ├── __init__.py
│       ├── agent.py          # 核心 Agent 实现
│       └── cli.py            # CLI 入口
├── examples/
│   ├── basic_usage.py        # 基本使用示例
│   ├── extract_article.py    # 文章提取示例
│   └── interactive_chat.py   # 交互式对话示例
├── pyproject.toml
└── README.md
```

## 使用方式

### 作为库使用

```python
import asyncio
from skills_agent import SkillsAgent
from claude_agent_sdk import AssistantMessage, TextBlock

async def main():
    agent = SkillsAgent()

    async for message in agent.run("提取这篇公众号文章"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

asyncio.run(main())
```

### 作为 CLI 使用

```bash
# 单次执行
skills-agent "你的请求"

# 交互式模式
skills-agent --interactive
```

## Skills 位置

Agent 会自动发现以下位置的 Skills：

- `~/.claude/skills/` - 用户级 Skills（全局可用）
- `.claude/skills/` - 项目级 Skills（项目特定）

每个 Skill 目录需要包含 `SKILL.md` 文件，格式如下：

```markdown
---
name: my-skill
description: 这个 Skill 做什么，什么时候使用它
---

# My Skill

## 使用说明

...
```

## 参考文档

- [skill_introduce.md](./skill_introduce.md) - Skills 详细介绍
- [agent_sdk_overview.md](./agent_sdk_overview.md) - Agent SDK 概述
- [agent_sdk_python.md](./agent_sdk_python.md) - Python SDK API 参考

## License

MIT
