# LangChain Skills Agent

使用 LangChain 构建的能发现和使用 Skills 的 Coding Agent，演示 Anthropic Skills 三层加载机制的底层原理。

## 核心概念

### 什么是 Skills？

Skills 是 Claude Code 的模块化能力扩展机制。每个 Skill 打包了指令、元数据和可选资源（脚本、模板），Agent 会在相关时自动使用它们。

### Skills 三层加载机制

| 层级 | 加载时机 | Token 消耗 | 内容 |
|------|----------|------------|------|
| **Level 1** | 启动时 | ~100/Skill | YAML frontmatter (name, description) |
| **Level 2** | 触发时 | <5000 | SKILL.md 主体指令 |
| **Level 3** | 按需 | 仅输出 | 脚本执行结果（代码不进上下文） |

### 核心设计理念

```
让大模型成为真正的"智能体"：
- 自己阅读 SKILL.md 指令
- 自己发现可用的脚本
- 自己决定执行什么命令
- 代码层面不需要特殊处理脚本发现/执行逻辑
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

# 三层加载机制演示
uv run python examples/langchain_demo.py

# 或使用 CLI
uv run langchain-skills --list-skills
uv run langchain-skills --show-prompt
uv run langchain-skills --interactive
```

## 项目结构

```
skills-agent-proto/
├── src/
│   └── langchain_skills/
│       ├── __init__.py       # 模块导出
│       ├── agent.py          # LangChain Agent 实现
│       ├── cli.py            # CLI 入口
│       ├── skill_loader.py   # Skills 发现和加载
│       └── tools.py          # LangChain Tools 定义
├── examples/
│   ├── basic_usage.py        # 基本使用示例
│   ├── extract_article.py    # 文章提取示例
│   ├── interactive_chat.py   # 交互式对话示例
│   └── langchain_demo.py     # 三层加载机制演示
├── pyproject.toml
└── README.md
```

## 使用方式

### 作为库使用

```python
from langchain_skills import LangChainSkillsAgent

# 创建 Agent
agent = LangChainSkillsAgent()

# 查看发现的 Skills
for skill in agent.get_discovered_skills():
    print(f"- {skill['name']}: {skill['description']}")

# 查看 system prompt (Level 1)
print(agent.get_system_prompt())

# 运行 Agent
result = agent.invoke("提取这篇公众号文章")
response = agent.get_last_response(result)
print(response)
```

### 作为 CLI 使用

```bash
# 列出发现的 Skills
langchain-skills --list-skills

# 显示 system prompt
langchain-skills --show-prompt

# 交互式模式
langchain-skills --interactive
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

## LangChain 1.0 API 要点

### create_agent

```python
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

agent = create_agent(
    model=ChatAnthropic(model="claude-sonnet-4-5-20250929"),
    tools=[load_skill, bash, read_file],
    system_prompt=skills_prompt,
)
```

### @tool with ToolRuntime

```python
from langchain.tools import tool, ToolRuntime

@tool
def my_tool(arg: str, runtime: ToolRuntime[MyContext]) -> str:
    '''Tool description.'''
    # runtime.context 访问上下文
    return result
```

## 参考文档

- [skill_introduce.md](./skill_introduce.md) - Skills 详细介绍
- [langchain_agent_skill.md](./langchain_agent_skill.md) - LangChain 实现说明

## License

MIT
