# Agent SDK overview
# Agent SDK 概述

Build production AI agents with Claude Code as a library
使用 Claude Code 作为库构建生产级 AI 智能体

---

<Note>
The Claude Code SDK has been renamed to the Claude Agent SDK. If you're migrating from the old SDK, see the [Migration Guide](/docs/en/agent-sdk/migration-guide).
Claude Code SDK 已更名为 Claude Agent SDK。如果你正在从旧 SDK 迁移，请参阅[迁移指南](/docs/en/agent-sdk/migration-guide)。
</Note>

Build AI agents that autonomously read files, run commands, search the web, edit code, and more. The Agent SDK gives you the same tools, agent loop, and context management that power Claude Code, programmable in Python and TypeScript.
构建能够自主读取文件、运行命令、搜索网页、编辑代码等的 AI 智能体。Agent SDK 为你提供与 Claude Code 相同的工具、智能体循环和上下文管理能力，可在 Python 和 TypeScript 中编程使用。

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find and fix the bug in auth.py",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"])
    ):
        print(message)  # Claude reads the file, finds the bug, edits it
                        # Claude 读取文件，找到 bug，修复它

asyncio.run(main())
```

The Agent SDK includes built-in tools for reading files, running commands, and editing code, so your agent can start working immediately without you implementing tool execution. Dive into the quickstart or explore real agents built with the SDK:
Agent SDK 包含用于读取文件、运行命令和编辑代码的内置工具，因此你的智能体可以立即开始工作，无需你实现工具执行。深入快速入门或探索使用 SDK 构建的真实智能体：

- [Quickstart](/docs/en/agent-sdk/quickstart) - Build a bug-fixing agent in minutes
- [快速入门](/docs/en/agent-sdk/quickstart) - 在几分钟内构建一个修复 bug 的智能体
- [Example agents](https://github.com/anthropics/claude-agent-sdk-demos) - Email assistant, research agent, and more
- [示例智能体](https://github.com/anthropics/claude-agent-sdk-demos) - 邮件助手、研究智能体等

## Capabilities
## 能力

Everything that makes Claude Code powerful is available in the SDK:
使 Claude Code 强大的一切都可以在 SDK 中使用：

### Built-in tools
### 内置工具

Your agent can read files, run commands, and search codebases out of the box. Key tools include:
你的智能体可以开箱即用地读取文件、运行命令和搜索代码库。主要工具包括：

| Tool | What it does |
| 工具 | 功能描述 |
|------|--------------|
| **Read** | Read any file in the working directory |
| **Read** | 读取工作目录中的任何文件 |
| **Write** | Create new files |
| **Write** | 创建新文件 |
| **Edit** | Make precise edits to existing files |
| **Edit** | 对现有文件进行精确编辑 |
| **Bash** | Run terminal commands, scripts, git operations |
| **Bash** | 运行终端命令、脚本、git 操作 |
| **Glob** | Find files by pattern (`**/*.ts`, `src/**/*.py`) |
| **Glob** | 按模式查找文件（`**/*.ts`、`src/**/*.py`） |
| **Grep** | Search file contents with regex |
| **Grep** | 使用正则表达式搜索文件内容 |
| **WebSearch** | Search the web for current information |
| **WebSearch** | 在网络上搜索当前信息 |
| **WebFetch** | Fetch and parse web page content |
| **WebFetch** | 获取和解析网页内容 |
| **AskUserQuestion** | Ask the user clarifying questions with multiple choice options |
| **AskUserQuestion** | 向用户提出带有多选项的澄清问题 |

This example creates an agent that searches your codebase for TODO comments:
这个示例创建了一个在代码库中搜索 TODO 注释的智能体：

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find all TODO comments and create a summary",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"])
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

### Hooks
### 钩子

Run custom code at key points in the agent lifecycle. SDK hooks use callback functions to validate, log, block, or transform agent behavior.
在智能体生命周期的关键点运行自定义代码。SDK 钩子使用回调函数来验证、记录、阻止或转换智能体行为。

**Available hooks:** `PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, and more.
**可用钩子：** `PreToolUse`、`PostToolUse`、`Stop`、`SessionStart`、`SessionEnd`、`UserPromptSubmit` 等。

This example logs all file changes to an audit file:
这个示例将所有文件更改记录到审计文件中：

```python
import asyncio
from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher

async def log_file_change(input_data, tool_use_id, context):
    file_path = input_data.get('tool_input', {}).get('file_path', 'unknown')
    with open('./audit.log', 'a') as f:
        f.write(f"{datetime.now()}: modified {file_path}\n")
    return {}

async def main():
    async for message in query(
        prompt="Refactor utils.py to improve readability",
        options=ClaudeAgentOptions(
            permission_mode="acceptEdits",
            hooks={
                "PostToolUse": [HookMatcher(matcher="Edit|Write", hooks=[log_file_change])]
            }
        )
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

[Learn more about hooks →](/docs/en/agent-sdk/hooks)
[了解更多关于钩子的信息 →](/docs/en/agent-sdk/hooks)

### Subagents
### 子智能体

Spawn specialized agents to handle focused subtasks. Your main agent delegates work, and subagents report back with results.
生成专门的智能体来处理集中的子任务。你的主智能体委派工作，子智能体返回结果。

Define custom agents with specialized instructions. Include `Task` in `allowedTools` since subagents are invoked via the Task tool:
使用专门的指令定义自定义智能体。在 `allowedTools` 中包含 `Task`，因为子智能体是通过 Task 工具调用的：

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async def main():
    async for message in query(
        prompt="Use the code-reviewer agent to review this codebase",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep", "Task"],
            agents={
                "code-reviewer": AgentDefinition(
                    description="Expert code reviewer for quality and security reviews.",
                    prompt="Analyze code quality and suggest improvements.",
                    tools=["Read", "Glob", "Grep"]
                )
            }
        )
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

Messages from within a subagent's context include a `parent_tool_use_id` field, letting you track which messages belong to which subagent execution.
来自子智能体上下文的消息包含 `parent_tool_use_id` 字段，让你可以跟踪哪些消息属于哪个子智能体执行。

[Learn more about subagents →](/docs/en/agent-sdk/subagents)
[了解更多关于子智能体的信息 →](/docs/en/agent-sdk/subagents)

### MCP

Connect to external systems via the Model Context Protocol: databases, browsers, APIs, and [hundreds more](https://github.com/modelcontextprotocol/servers).
通过模型上下文协议连接到外部系统：数据库、浏览器、API 和[更多](https://github.com/modelcontextprotocol/servers)。

This example connects the [Playwright MCP server](https://github.com/microsoft/playwright-mcp) to give your agent browser automation capabilities:
这个示例连接 [Playwright MCP 服务器](https://github.com/microsoft/playwright-mcp)为你的智能体提供浏览器自动化能力：

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Open example.com and describe what you see",
        options=ClaudeAgentOptions(
            mcp_servers={
                "playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]}
            }
        )
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

[Learn more about MCP →](/docs/en/agent-sdk/mcp)
[了解更多关于 MCP 的信息 →](/docs/en/agent-sdk/mcp)

### Permissions
### 权限

Control exactly which tools your agent can use. Allow safe operations, block dangerous ones, or require approval for sensitive actions.
精确控制你的智能体可以使用哪些工具。允许安全操作，阻止危险操作，或要求批准敏感操作。

This example creates a read-only agent that can analyze but not modify code:
这个示例创建了一个只能分析但不能修改代码的只读智能体：

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Review this code for best practices",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="bypassPermissions"
        )
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

[Learn more about permissions →](/docs/en/agent-sdk/permissions)
[了解更多关于权限的信息 →](/docs/en/agent-sdk/permissions)

### Sessions
### 会话

Maintain context across multiple exchanges. Claude remembers files read, analysis done, and conversation history. Resume sessions later, or fork them to explore different approaches.
跨多次交换维护上下文。Claude 记住读取的文件、完成的分析和对话历史。稍后恢复会话，或分叉它们以探索不同的方法。

This example captures the session ID from the first query, then resumes to continue with full context:
这个示例从第一次查询中捕获会话 ID，然后恢复以继续完整的上下文：

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    session_id = None

    # First query: capture the session ID
    # 第一次查询：捕获会话 ID
    async for message in query(
        prompt="Read the authentication module",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Glob"])
    ):
        if hasattr(message, 'subtype') and message.subtype == 'init':
            session_id = message.session_id

    # Resume with full context from the first query
    # 使用第一次查询的完整上下文恢复
    async for message in query(
        prompt="Now find all places that call it",  # "it" = auth module
        options=ClaudeAgentOptions(resume=session_id)
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

[Learn more about sessions →](/docs/en/agent-sdk/sessions)
[了解更多关于会话的信息 →](/docs/en/agent-sdk/sessions)

### Claude Code features
### Claude Code 功能

The SDK also supports Claude Code's filesystem-based configuration. To use these features, set `setting_sources=["project"]` (Python) or `settingSources: ['project']` (TypeScript) in your options.
SDK 还支持 Claude Code 的基于文件系统的配置。要使用这些功能，请在选项中设置 `setting_sources=["project"]`（Python）或 `settingSources: ['project']`（TypeScript）。

| Feature | Description | Location |
| 功能 | 描述 | 位置 |
|---------|-------------|----------|
| [Skills](/docs/en/agent-sdk/skills) | Specialized capabilities defined in Markdown | `.claude/skills/SKILL.md` |
| [Skills](/docs/en/agent-sdk/skills) | 在 Markdown 中定义的专业能力 | `.claude/skills/SKILL.md` |
| [Slash commands](/docs/en/agent-sdk/slash-commands) | Custom commands for common tasks | `.claude/commands/*.md` |
| [斜杠命令](/docs/en/agent-sdk/slash-commands) | 用于常见任务的自定义命令 | `.claude/commands/*.md` |
| [Memory](/docs/en/agent-sdk/modifying-system-prompts) | Project context and instructions | `CLAUDE.md` or `.claude/CLAUDE.md` |
| [Memory](/docs/en/agent-sdk/modifying-system-prompts) | 项目上下文和指令 | `CLAUDE.md` 或 `.claude/CLAUDE.md` |
| [Plugins](/docs/en/agent-sdk/plugins) | Extend with custom commands, agents, and MCP servers | Programmatic via `plugins` option |
| [插件](/docs/en/agent-sdk/plugins) | 使用自定义命令、智能体和 MCP 服务器扩展 | 通过 `plugins` 选项编程配置 |

## Get started
## 开始使用

### Step 1: Install Claude Code
### 步骤 1：安装 Claude Code

The SDK uses Claude Code as its runtime:
SDK 使用 Claude Code 作为其运行时：

**macOS/Linux/WSL:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Homebrew:**
```bash
brew install --cask claude-code
```

**WinGet:**
```powershell
winget install Anthropic.ClaudeCode
```

See [Claude Code setup](https://code.claude.com/docs/en/setup) for Windows and other options.
有关 Windows 和其他选项，请参阅 [Claude Code 设置](https://code.claude.com/docs/en/setup)。

### Step 2: Install the SDK
### 步骤 2：安装 SDK

**TypeScript:**
```bash
npm install @anthropic-ai/claude-agent-sdk
```

**Python:**
```bash
pip install claude-agent-sdk
```

### Step 3: Set your API key
### 步骤 3：设置 API 密钥

```bash
export ANTHROPIC_API_KEY=your-api-key
```

Get your key from the [Console](https://platform.claude.com/).
从 [Console](https://platform.claude.com/) 获取你的密钥。

The SDK also supports authentication via third-party API providers:
SDK 还支持通过第三方 API 提供商进行身份验证：

- **Amazon Bedrock**: set `CLAUDE_CODE_USE_BEDROCK=1` environment variable and configure AWS credentials
- **Amazon Bedrock**：设置 `CLAUDE_CODE_USE_BEDROCK=1` 环境变量并配置 AWS 凭证
- **Google Vertex AI**: set `CLAUDE_CODE_USE_VERTEX=1` environment variable and configure Google Cloud credentials
- **Google Vertex AI**：设置 `CLAUDE_CODE_USE_VERTEX=1` 环境变量并配置 Google Cloud 凭证
- **Microsoft Foundry**: set `CLAUDE_CODE_USE_FOUNDRY=1` environment variable and configure Azure credentials
- **Microsoft Foundry**：设置 `CLAUDE_CODE_USE_FOUNDRY=1` 环境变量并配置 Azure 凭证

<Note>
Unless previously approved, we do not allow third party developers to offer Claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK. Please use the API key authentication methods described in this document instead.
除非事先获得批准，否则我们不允许第三方开发者为其产品（包括基于 Claude Agent SDK 构建的智能体）提供 Claude.ai 登录或速率限制。请改用本文档中描述的 API 密钥身份验证方法。
</Note>

### Step 4: Run your first agent
### 步骤 4：运行你的第一个智能体

This example creates an agent that lists files in your current directory using built-in tools.
这个示例创建了一个使用内置工具列出当前目录中文件的智能体。

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="What files are in this directory?",
        options=ClaudeAgentOptions(allowed_tools=["Bash", "Glob"])
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

**Ready to build?** Follow the [Quickstart](/docs/en/agent-sdk/quickstart) to create an agent that finds and fixes bugs in minutes.
**准备好构建了吗？** 按照[快速入门](/docs/en/agent-sdk/quickstart)在几分钟内创建一个查找并修复 bug 的智能体。

## Compare the Agent SDK to other Claude tools
## 将 Agent SDK 与其他 Claude 工具进行比较

The Claude platform offers multiple ways to build with Claude. Here's how the Agent SDK fits in:
Claude 平台提供多种方式来使用 Claude 构建。以下是 Agent SDK 的定位：

### Agent SDK vs Client SDK
### Agent SDK vs Client SDK（客户端 SDK）

The [Anthropic Client SDK](/docs/en/api/client-sdks) gives you direct API access: you send prompts and implement tool execution yourself. The **Agent SDK** gives you Claude with built-in tool execution.
[Anthropic Client SDK](/docs/en/api/client-sdks) 为你提供直接的 API 访问：你发送提示并自己实现工具执行。**Agent SDK** 为你提供具有内置工具执行的 Claude。

With the Client SDK, you implement a tool loop. With the Agent SDK, Claude handles it:
使用 Client SDK，你需要实现工具循环。使用 Agent SDK，Claude 会处理它：

```python
# Client SDK: You implement the tool loop
# Client SDK：你实现工具循环
response = client.messages.create(...)
while response.stop_reason == "tool_use":
    result = your_tool_executor(response.tool_use)
    response = client.messages.create(tool_result=result, ...)

# Agent SDK: Claude handles tools autonomously
# Agent SDK：Claude 自主处理工具
async for message in query(prompt="Fix the bug in auth.py"):
    print(message)
```

### Agent SDK vs Claude Code CLI
### Agent SDK vs Claude Code CLI（命令行工具）

Same capabilities, different interface:
相同的能力，不同的接口：

| Use case | Best choice |
| 使用场景 | 最佳选择 |
|----------|-------------|
| Interactive development | CLI |
| 交互式开发 | CLI |
| CI/CD pipelines | SDK |
| CI/CD 管道 | SDK |
| Custom applications | SDK |
| 自定义应用程序 | SDK |
| One-off tasks | CLI |
| 一次性任务 | CLI |
| Production automation | SDK |
| 生产自动化 | SDK |

Many teams use both: CLI for daily development, SDK for production. Workflows translate directly between them.
许多团队同时使用两者：CLI 用于日常开发，SDK 用于生产。工作流程可以直接在两者之间转换。

## Changelog
## 更新日志

View the full changelog for SDK updates, bug fixes, and new features:
查看 SDK 更新、错误修复和新功能的完整更新日志：

- **TypeScript SDK**: [view CHANGELOG.md](https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md)
- **TypeScript SDK**：[查看 CHANGELOG.md](https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md)
- **Python SDK**: [view CHANGELOG.md](https://github.com/anthropics/claude-agent-sdk-python/blob/main/CHANGELOG.md)
- **Python SDK**：[查看 CHANGELOG.md](https://github.com/anthropics/claude-agent-sdk-python/blob/main/CHANGELOG.md)

## Reporting bugs
## 报告 bug

If you encounter bugs or issues with the Agent SDK:
如果你遇到 Agent SDK 的 bug 或问题：

- **TypeScript SDK**: [report issues on GitHub](https://github.com/anthropics/claude-agent-sdk-typescript/issues)
- **TypeScript SDK**：[在 GitHub 上报告问题](https://github.com/anthropics/claude-agent-sdk-typescript/issues)
- **Python SDK**: [report issues on GitHub](https://github.com/anthropics/claude-agent-sdk-python/issues)
- **Python SDK**：[在 GitHub 上报告问题](https://github.com/anthropics/claude-agent-sdk-python/issues)

## Branding guidelines
## 品牌指南

For partners integrating the Claude Agent SDK, use of Claude branding is optional. When referencing Claude in your product:
对于集成 Claude Agent SDK 的合作伙伴，使用 Claude 品牌是可选的。在产品中引用 Claude 时：

**Allowed:**
**允许：**
- "Claude Agent" (preferred for dropdown menus)
- "Claude Agent"（下拉菜单的首选）
- "Claude" (when within a menu already labeled "Agents")
- "Claude"（当在已标记为"Agents"的菜单中时）
- "{YourAgentName} Powered by Claude" (if you have an existing agent name)
- "{你的智能体名称} Powered by Claude"（如果你有现有的智能体名称）

**Not permitted:**
**不允许：**
- "Claude Code" or "Claude Code Agent"
- "Claude Code" 或 "Claude Code Agent"
- Claude Code-branded ASCII art or visual elements that mimic Claude Code
- Claude Code 品牌的 ASCII 艺术或模仿 Claude Code 的视觉元素

Your product should maintain its own branding and not appear to be Claude Code or any Anthropic product. For questions about branding compliance, contact our [sales team](https://www.anthropic.com/contact-sales).
你的产品应保持自己的品牌，不应看起来像是 Claude Code 或任何 Anthropic 产品。有关品牌合规性的问题，请联系我们的[销售团队](https://www.anthropic.com/contact-sales)。

## License and terms
## 许可证和条款

Use of the Claude Agent SDK is governed by [Anthropic's Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms), including when you use it to power products and services that you make available to your own customers and end users, except to the extent a specific component or dependency is covered by a different license as indicated in that component's LICENSE file.
Claude Agent SDK 的使用受 [Anthropic 商业服务条款](https://www.anthropic.com/legal/commercial-terms)约束，包括当你使用它为你自己的客户和最终用户提供产品和服务时，除非特定组件或依赖项在其 LICENSE 文件中指明受不同许可证的约束。

## Next steps
## 下一步

- [Quickstart](/docs/en/agent-sdk/quickstart) - Build an agent that finds and fixes bugs in minutes
- [快速入门](/docs/en/agent-sdk/quickstart) - 在几分钟内构建一个查找并修复 bug 的智能体
- [Example agents](https://github.com/anthropics/claude-agent-sdk-demos) - Email assistant, research agent, and more
- [示例智能体](https://github.com/anthropics/claude-agent-sdk-demos) - 邮件助手、研究智能体等
- [TypeScript SDK](/docs/en/agent-sdk/typescript) - Full TypeScript API reference and examples
- [TypeScript SDK](/docs/en/agent-sdk/typescript) - 完整的 TypeScript API 参考和示例
- [Python SDK](/docs/en/agent-sdk/python) - Full Python API reference and examples
- [Python SDK](/docs/en/agent-sdk/python) - 完整的 Python API 参考和示例
