# LangChain Skills Agent

使用 LangChain 构建的能发现和使用 Skills 的 Coding Agent，演示 Anthropic Skills 三层加载机制的底层原理。

> **B站视频演示**: 配合视频《Skills 原理深度解析 + Agent 实战》使用，一键三连换代码！

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
# 或使用 CLI
uv run langchain-skills --list-skills
uv run langchain-skills --show-prompt
uv run langchain-skills --interactive
```

## 视频演示命令

以下命令用于 B 站视频演示，展示三层加载机制：

```bash
# 1. 列出 Skills（展示 Level 1 元数据发现）
uv run langchain-skills --list-skills

# 2. 显示 System Prompt（展示元数据注入）
uv run langchain-skills --show-prompt

# 3. 实际运行（展示 Level 2 + 3 加载过程）
uv run langchain-skills "提取这篇公众号文章: https://mp.weixin.qq.com/s/xxx"
```

### 示例 Skill: news-extractor

项目自带的演示 Skill，位于 `.claude/skills/news-extractor/`:

```
.claude/skills/news-extractor/
├── SKILL.md              # 元数据 + 指令
├── pyproject.toml        # 依赖配置
└── scripts/
    └── extract_news.py   # 提取脚本
```

支持的站点：
- 微信公众号 (`mp.weixin.qq.com`)
- 今日头条 (`toutiao.com`)
- 网易新闻 (`163.com`)
- 搜狐新闻 (`sohu.com`)
- 腾讯新闻 (`qq.com`)

## 项目结构

```
skills-agent-proto/
├── .claude/
│   └── skills/
│       └── news-extractor/   # 示例 Skill
│           ├── SKILL.md
│           ├── pyproject.toml
│           └── scripts/
│               └── extract_news.py
├── src/
│   └── langchain_skills/
│       ├── __init__.py       # 模块导出
│       ├── agent.py          # LangChain Agent 实现（Level 1 注入）
│       ├── cli.py            # CLI 入口（流式输出 + Thinking）
│       ├── skill_loader.py   # Skills 发现和加载（三层加载核心）
│       └── tools.py          # LangChain Tools（load_skill + bash）
├── examples/                  # 示例代码
│   ├── basic_usage.py
│   ├── extract_article.py
│   ├── interactive_chat.py
│   └── langchain_demo.py
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
