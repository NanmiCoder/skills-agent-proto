# Agent SDK reference - Python
# Agent SDK 参考 - Python

Complete API reference for the Python Agent SDK, including all functions, types, and classes.
Python Agent SDK 的完整 API 参考，包括所有函数、类型和类。

---

## Installation
## 安装

```bash
pip install claude-agent-sdk
```

## Choosing Between `query()` and `ClaudeSDKClient`
## 选择 `query()` 还是 `ClaudeSDKClient`

The Python SDK provides two ways to interact with Claude Code:
Python SDK 提供两种与 Claude Code 交互的方式：

### Quick Comparison
### 快速比较

| Feature | `query()` | `ClaudeSDKClient` |
| 功能 | `query()` | `ClaudeSDKClient` |
| :------------------ | :---------------------------- | :--------------------------------- |
| **Session** | Creates new session each time | Reuses same session |
| **会话** | 每次创建新会话 | 重用同一会话 |
| **Conversation** | Single exchange | Multiple exchanges in same context |
| **对话** | 单次交换 | 同一上下文中的多次交换 |
| **Connection** | Managed automatically | Manual control |
| **连接** | 自动管理 | 手动控制 |
| **Streaming Input** | Supported | Supported |
| **流式输入** | 支持 | 支持 |
| **Interrupts** | Not supported | Supported |
| **中断** | 不支持 | 支持 |
| **Hooks** | Not supported | Supported |
| **钩子** | 不支持 | 支持 |
| **Custom Tools** | Not supported | Supported |
| **自定义工具** | 不支持 | 支持 |
| **Continue Chat** | New session each time | Maintains conversation |
| **继续聊天** | 每次新会话 | 保持对话 |
| **Use Case** | One-off tasks | Continuous conversations |
| **使用场景** | 一次性任务 | 持续对话 |

### When to Use `query()` (New Session Each Time)
### 何时使用 `query()`（每次新会话）

**Best for:**
**最适合：**

- One-off questions where you don't need conversation history
- 不需要对话历史的一次性问题
- Independent tasks that don't require context from previous exchanges
- 不需要先前交换上下文的独立任务
- Simple automation scripts
- 简单的自动化脚本
- When you want a fresh start each time
- 当你每次都想重新开始时

### When to Use `ClaudeSDKClient` (Continuous Conversation)
### 何时使用 `ClaudeSDKClient`（持续对话）

**Best for:**
**最适合：**

- **Continuing conversations** - When you need Claude to remember context
- **继续对话** - 当你需要 Claude 记住上下文时
- **Follow-up questions** - Building on previous responses
- **后续问题** - 基于先前的回复
- **Interactive applications** - Chat interfaces, REPLs
- **交互式应用程序** - 聊天界面、REPL
- **Response-driven logic** - When next action depends on Claude's response
- **响应驱动逻辑** - 当下一步操作取决于 Claude 的回复时
- **Session control** - Managing conversation lifecycle explicitly
- **会话控制** - 明确管理对话生命周期

## Functions
## 函数

### `query()`

Creates a new session for each interaction with Claude Code. Returns an async iterator that yields messages as they arrive. Each call to `query()` starts fresh with no memory of previous interactions.
为与 Claude Code 的每次交互创建新会话。返回一个异步迭代器，在消息到达时产出消息。每次调用 `query()` 都会重新开始，没有先前交互的记忆。

```python
async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None
) -> AsyncIterator[Message]
```

#### Parameters
#### 参数

| Parameter | Type | Description |
| 参数 | 类型 | 描述 |
| :-------- | :--------------------------- | :------------------------------------------------------------------------- |
| `prompt` | `str \| AsyncIterable[dict]` | The input prompt as a string or async iterable for streaming mode |
| `prompt` | `str \| AsyncIterable[dict]` | 输入提示，可以是字符串或用于流式模式的异步可迭代对象 |
| `options` | `ClaudeAgentOptions \| None` | Optional configuration object (defaults to `ClaudeAgentOptions()` if None) |
| `options` | `ClaudeAgentOptions \| None` | 可选配置对象（如果为 None 则默认为 `ClaudeAgentOptions()`） |

#### Returns
#### 返回值

Returns an `AsyncIterator[Message]` that yields messages from the conversation.
返回一个 `AsyncIterator[Message]`，产出对话中的消息。

#### Example - With options
#### 示例 - 带选项

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are an expert Python developer",
        permission_mode='acceptEdits',
        cwd="/home/user/project"
    )

    async for message in query(
        prompt="Create a Python web server",
        options=options
    ):
        print(message)

asyncio.run(main())
```

### `tool()`

Decorator for defining MCP tools with type safety.
用于定义具有类型安全的 MCP 工具的装饰器。

```python
def tool(
    name: str,
    description: str,
    input_schema: type | dict[str, Any]
) -> Callable[[Callable[[Any], Awaitable[dict[str, Any]]]], SdkMcpTool[Any]]
```

#### Parameters
#### 参数

| Parameter | Type | Description |
| 参数 | 类型 | 描述 |
| :------------- | :----------------------- | :------------------------------------------------------ |
| `name` | `str` | Unique identifier for the tool |
| `name` | `str` | 工具的唯一标识符 |
| `description` | `str` | Human-readable description of what the tool does |
| `description` | `str` | 工具功能的人类可读描述 |
| `input_schema` | `type \| dict[str, Any]` | Schema defining the tool's input parameters |
| `input_schema` | `type \| dict[str, Any]` | 定义工具输入参数的模式 |

#### Input Schema Options
#### 输入模式选项

1. **Simple type mapping** (recommended):
1. **简单类型映射**（推荐）：

```python
{"text": str, "count": int, "enabled": bool}
```

2. **JSON Schema format** (for complex validation):
2. **JSON Schema 格式**（用于复杂验证）：

```python
{
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "count": {"type": "integer", "minimum": 0}
    },
    "required": ["text"]
}
```

#### Example
#### 示例

```python
from claude_agent_sdk import tool
from typing import Any

@tool("greet", "Greet a user", {"name": str})
async def greet(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{
            "type": "text",
            "text": f"Hello, {args['name']}!"
        }]
    }
```

### `create_sdk_mcp_server()`

Create an in-process MCP server that runs within your Python application.
创建一个在 Python 应用程序中运行的进程内 MCP 服务器。

```python
def create_sdk_mcp_server(
    name: str,
    version: str = "1.0.0",
    tools: list[SdkMcpTool[Any]] | None = None
) -> McpSdkServerConfig
```

#### Parameters
#### 参数

| Parameter | Type | Default | Description |
| 参数 | 类型 | 默认值 | 描述 |
| :-------- | :------------------------------ | :-------- | :---------------------------------------------------- |
| `name` | `str` | - | Unique identifier for the server |
| `name` | `str` | - | 服务器的唯一标识符 |
| `version` | `str` | `"1.0.0"` | Server version string |
| `version` | `str` | `"1.0.0"` | 服务器版本字符串 |
| `tools` | `list[SdkMcpTool[Any]] \| None` | `None` | List of tool functions created with `@tool` decorator |
| `tools` | `list[SdkMcpTool[Any]] \| None` | `None` | 使用 `@tool` 装饰器创建的工具函数列表 |

#### Example
#### 示例

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {
        "content": [{
            "type": "text",
            "text": f"Sum: {args['a'] + args['b']}"
        }]
    }

@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args):
    return {
        "content": [{
            "type": "text",
            "text": f"Product: {args['a'] * args['b']}"
        }]
    }

calculator = create_sdk_mcp_server(
    name="calculator",
    version="2.0.0",
    tools=[add, multiply]  # Pass decorated functions
                           # 传递装饰的函数
)

# Use with Claude
# 与 Claude 一起使用
options = ClaudeAgentOptions(
    mcp_servers={"calc": calculator},
    allowed_tools=["mcp__calc__add", "mcp__calc__multiply"]
)
```

## Classes
## 类

### `ClaudeSDKClient`

**Maintains a conversation session across multiple exchanges.** This is the Python equivalent of how the TypeScript SDK's `query()` function works internally - it creates a client object that can continue conversations.
**在多次交换中维护对话会话。** 这是 TypeScript SDK 的 `query()` 函数内部工作方式的 Python 等效项 - 它创建一个可以继续对话的客户端对象。

#### Key Features
#### 主要功能

- **Session Continuity**: Maintains conversation context across multiple `query()` calls
- **会话连续性**：在多次 `query()` 调用之间维护对话上下文
- **Same Conversation**: Claude remembers previous messages in the session
- **同一对话**：Claude 记住会话中的先前消息
- **Interrupt Support**: Can stop Claude mid-execution
- **中断支持**：可以在执行过程中停止 Claude
- **Explicit Lifecycle**: You control when the session starts and ends
- **明确的生命周期**：你控制会话何时开始和结束
- **Response-driven Flow**: Can react to responses and send follow-ups
- **响应驱动流程**：可以对响应做出反应并发送后续消息
- **Custom Tools & Hooks**: Supports custom tools and hooks
- **自定义工具和钩子**：支持自定义工具和钩子

```python
class ClaudeSDKClient:
    def __init__(self, options: ClaudeAgentOptions | None = None)
    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None
    async def query(self, prompt: str | AsyncIterable[dict], session_id: str = "default") -> None
    async def receive_messages(self) -> AsyncIterator[Message]
    async def receive_response(self) -> AsyncIterator[Message]
    async def interrupt(self) -> None
    async def rewind_files(self, user_message_uuid: str) -> None
    async def disconnect(self) -> None
```

#### Methods
#### 方法

| Method | Description |
| 方法 | 描述 |
| :-------------------------- | :------------------------------------------------------------------ |
| `__init__(options)` | Initialize the client with optional configuration |
| `__init__(options)` | 使用可选配置初始化客户端 |
| `connect(prompt)` | Connect to Claude with an optional initial prompt or message stream |
| `connect(prompt)` | 使用可选的初始提示或消息流连接到 Claude |
| `query(prompt, session_id)` | Send a new request in streaming mode |
| `query(prompt, session_id)` | 在流式模式下发送新请求 |
| `receive_messages()` | Receive all messages from Claude as an async iterator |
| `receive_messages()` | 作为异步迭代器接收来自 Claude 的所有消息 |
| `receive_response()` | Receive messages until and including a ResultMessage |
| `receive_response()` | 接收消息直到并包括 ResultMessage |
| `interrupt()` | Send interrupt signal (only works in streaming mode) |
| `interrupt()` | 发送中断信号（仅在流式模式下有效） |
| `rewind_files(user_message_uuid)` | Restore files to their state at the specified user message |
| `rewind_files(user_message_uuid)` | 将文件恢复到指定用户消息时的状态 |
| `disconnect()` | Disconnect from Claude |
| `disconnect()` | 断开与 Claude 的连接 |

#### Context Manager Support
#### 上下文管理器支持

The client can be used as an async context manager for automatic connection management:
客户端可以用作异步上下文管理器以实现自动连接管理：

```python
async with ClaudeSDKClient() as client:
    await client.query("Hello Claude")
    async for message in client.receive_response():
        print(message)
```

#### Example - Continuing a conversation
#### 示例 - 继续对话

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

async def main():
    async with ClaudeSDKClient() as client:
        # First question
        # 第一个问题
        await client.query("What's the capital of France?")

        # Process response
        # 处理响应
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # Follow-up question - Claude remembers the previous context
        # 后续问题 - Claude 记住之前的上下文
        await client.query("What's the population of that city?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # Another follow-up - still in the same conversation
        # 另一个后续 - 仍在同一对话中
        await client.query("What are some famous landmarks there?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

asyncio.run(main())
```

#### Example - Using interrupts
#### 示例 - 使用中断

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def interruptible_task():
    options = ClaudeAgentOptions(
        allowed_tools=["Bash"],
        permission_mode="acceptEdits"
    )

    async with ClaudeSDKClient(options=options) as client:
        # Start a long-running task
        # 启动一个长时间运行的任务
        await client.query("Count from 1 to 100 slowly")

        # Let it run for a bit
        # 让它运行一会儿
        await asyncio.sleep(2)

        # Interrupt the task
        # 中断任务
        await client.interrupt()
        print("Task interrupted!")

        # Send a new command
        # 发送新命令
        await client.query("Just say hello instead")

        async for message in client.receive_response():
            # Process the new response
            # 处理新响应
            pass

asyncio.run(interruptible_task())
```

## Types
## 类型

### `ClaudeAgentOptions`

Configuration dataclass for Claude Code queries.
Claude Code 查询的配置数据类。

```python
@dataclass
class ClaudeAgentOptions:
    tools: list[str] | ToolsPreset | None = None
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    max_budget_usd: float | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    # ... more options
    # ... 更多选项
```

#### Key Properties
#### 主要属性

| Property | Type | Default | Description |
| 属性 | 类型 | 默认值 | 描述 |
| :---------------------------- | :------------------------------------------- | :------------------- | :---------------------------------------------------------------------------------------------------------------------- |
| `allowed_tools` | `list[str]` | `[]` | List of allowed tool names |
| `allowed_tools` | `list[str]` | `[]` | 允许的工具名称列表 |
| `system_prompt` | `str \| SystemPromptPreset \| None` | `None` | System prompt configuration |
| `system_prompt` | `str \| SystemPromptPreset \| None` | `None` | 系统提示配置 |
| `mcp_servers` | `dict[str, McpServerConfig] \| str \| Path` | `{}` | MCP server configurations |
| `mcp_servers` | `dict[str, McpServerConfig] \| str \| Path` | `{}` | MCP 服务器配置 |
| `permission_mode` | `PermissionMode \| None` | `None` | Permission mode for tool usage |
| `permission_mode` | `PermissionMode \| None` | `None` | 工具使用的权限模式 |
| `resume` | `str \| None` | `None` | Session ID to resume |
| `resume` | `str \| None` | `None` | 要恢复的会话 ID |
| `max_turns` | `int \| None` | `None` | Maximum conversation turns |
| `max_turns` | `int \| None` | `None` | 最大对话轮数 |
| `max_budget_usd` | `float \| None` | `None` | Maximum budget in USD |
| `max_budget_usd` | `float \| None` | `None` | 最大预算（美元） |
| `model` | `str \| None` | `None` | Claude model to use |
| `model` | `str \| None` | `None` | 要使用的 Claude 模型 |
| `cwd` | `str \| Path \| None` | `None` | Current working directory |
| `cwd` | `str \| Path \| None` | `None` | 当前工作目录 |
| `hooks` | `dict[HookEvent, list[HookMatcher]] \| None` | `None` | Hook configurations |
| `hooks` | `dict[HookEvent, list[HookMatcher]] \| None` | `None` | 钩子配置 |
| `agents` | `dict[str, AgentDefinition] \| None` | `None` | Programmatically defined subagents |
| `agents` | `dict[str, AgentDefinition] \| None` | `None` | 程序定义的子智能体 |
| `setting_sources` | `list[SettingSource] \| None` | `None` | Which filesystem settings to load |
| `setting_sources` | `list[SettingSource] \| None` | `None` | 要加载的文件系统设置 |

### `PermissionMode`

Permission modes for controlling tool execution.
控制工具执行的权限模式。

```python
PermissionMode = Literal[
    "default",           # Standard permission behavior
                         # 标准权限行为
    "acceptEdits",       # Auto-accept file edits
                         # 自动接受文件编辑
    "plan",              # Planning mode - no execution
                         # 规划模式 - 不执行
    "bypassPermissions"  # Bypass all permission checks (use with caution)
                         # 绕过所有权限检查（谨慎使用）
]
```

### `AgentDefinition`

Configuration for a subagent defined programmatically.
程序定义的子智能体配置。

```python
@dataclass
class AgentDefinition:
    description: str     # Natural language description of when to use this agent
                         # 何时使用此智能体的自然语言描述
    prompt: str          # The agent's system prompt
                         # 智能体的系统提示
    tools: list[str] | None = None  # Array of allowed tool names
                                     # 允许的工具名称数组
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
                         # Model override for this agent
                         # 此智能体的模型覆盖
```

### `SettingSource`

Controls which filesystem-based configuration sources the SDK loads settings from.
控制 SDK 从哪些基于文件系统的配置源加载设置。

```python
SettingSource = Literal["user", "project", "local"]
```

| Value | Description | Location |
| 值 | 描述 | 位置 |
| :---------- | :------------------------------------------- | :---------------------------- |
| `"user"` | Global user settings | `~/.claude/settings.json` |
| `"user"` | 全局用户设置 | `~/.claude/settings.json` |
| `"project"` | Shared project settings (version controlled) | `.claude/settings.json` |
| `"project"` | 共享项目设置（版本控制） | `.claude/settings.json` |
| `"local"` | Local project settings (gitignored) | `.claude/settings.local.json` |
| `"local"` | 本地项目设置（gitignore） | `.claude/settings.local.json` |

## Message Types
## 消息类型

### `Message`

Union type of all possible messages.
所有可能消息的联合类型。

```python
Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage | StreamEvent
```

### `UserMessage`

User input message.
用户输入消息。

```python
@dataclass
class UserMessage:
    content: str | list[ContentBlock]
```

### `AssistantMessage`

Assistant response message with content blocks.
带有内容块的助手响应消息。

```python
@dataclass
class AssistantMessage:
    content: list[ContentBlock]
    model: str
```

### `SystemMessage`

System message with metadata.
带有元数据的系统消息。

```python
@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]
```

### `ResultMessage`

Final result message with cost and usage information.
带有成本和使用信息的最终结果消息。

```python
@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
    structured_output: Any = None
```

## Content Block Types
## 内容块类型

### `ContentBlock`

Union type of all content blocks.
所有内容块的联合类型。

```python
ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock
```

### `TextBlock`

Text content block.
文本内容块。

```python
@dataclass
class TextBlock:
    text: str
```

### `ToolUseBlock`

Tool use request block.
工具使用请求块。

```python
@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
```

### `ToolResultBlock`

Tool execution result block.
工具执行结果块。

```python
@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None
```

## Error Types
## 错误类型

### `ClaudeSDKError`

Base exception class for all SDK errors.
所有 SDK 错误的基础异常类。

```python
class ClaudeSDKError(Exception):
    """Base error for Claude SDK."""
    """Claude SDK 的基础错误。"""
```

### `CLINotFoundError`

Raised when Claude Code CLI is not installed or not found.
当 Claude Code CLI 未安装或未找到时引发。

```python
class CLINotFoundError(CLIConnectionError):
    def __init__(self, message: str = "Claude Code not found", cli_path: str | None = None):
        """
        Args:
            message: Error message (default: "Claude Code not found")
                     错误消息（默认："Claude Code not found"）
            cli_path: Optional path to the CLI that was not found
                      未找到的 CLI 的可选路径
        """
```

### `ProcessError`

Raised when the Claude Code process fails.
当 Claude Code 进程失败时引发。

```python
class ProcessError(ClaudeSDKError):
    def __init__(self, message: str, exit_code: int | None = None, stderr: str | None = None):
        self.exit_code = exit_code
        self.stderr = stderr
```

## Hook Types
## 钩子类型

### `HookEvent`

Supported hook event types.
支持的钩子事件类型。

```python
HookEvent = Literal[
    "PreToolUse",       # Called before tool execution
                        # 在工具执行前调用
    "PostToolUse",      # Called after tool execution
                        # 在工具执行后调用
    "UserPromptSubmit", # Called when user submits a prompt
                        # 当用户提交提示时调用
    "Stop",             # Called when stopping execution
                        # 当停止执行时调用
    "SubagentStop",     # Called when a subagent stops
                        # 当子智能体停止时调用
    "PreCompact"        # Called before message compaction
                        # 在消息压缩前调用
]
```

### `HookCallback`

Type definition for hook callback functions.
钩子回调函数的类型定义。

```python
HookCallback = Callable[
    [dict[str, Any], str | None, HookContext],
    Awaitable[dict[str, Any]]
]
```

Parameters:
参数：

- `input_data`: Hook-specific input data
- `input_data`：钩子特定的输入数据
- `tool_use_id`: Optional tool use identifier (for tool-related hooks)
- `tool_use_id`：可选的工具使用标识符（用于工具相关的钩子）
- `context`: Hook context with additional information
- `context`：带有附加信息的钩子上下文

### `HookMatcher`

Configuration for matching hooks to specific events or tools.
将钩子与特定事件或工具匹配的配置。

```python
@dataclass
class HookMatcher:
    matcher: str | None = None        # Tool name or pattern to match (e.g., "Bash", "Write|Edit")
                                      # 要匹配的工具名称或模式（例如 "Bash"、"Write|Edit"）
    hooks: list[HookCallback] = field(default_factory=list)  # List of callbacks to execute
                                                              # 要执行的回调列表
    timeout: float | None = None      # Timeout in seconds (default: 60)
                                      # 超时时间（秒）（默认：60）
```

## Built-in Tools Input/Output
## 内置工具输入/输出

### Bash

**Input:**
**输入：**

```python
{
    "command": str,                  # The command to execute
                                     # 要执行的命令
    "timeout": int | None,           # Optional timeout in milliseconds (max 600000)
                                     # 可选的超时时间（毫秒）（最大 600000）
    "description": str | None,       # Clear, concise description (5-10 words)
                                     # 清晰简洁的描述（5-10 个词）
    "run_in_background": bool | None # Set to true to run in background
                                     # 设置为 true 以在后台运行
}
```

**Output:**
**输出：**

```python
{
    "output": str,              # Combined stdout and stderr output
                                # 合并的 stdout 和 stderr 输出
    "exitCode": int,            # Exit code of the command
                                # 命令的退出码
    "killed": bool | None,      # Whether command was killed due to timeout
                                # 命令是否因超时而被终止
    "shellId": str | None       # Shell ID for background processes
                                # 后台进程的 Shell ID
}
```

### Read

**Input:**
**输入：**

```python
{
    "file_path": str,       # The absolute path to the file to read
                            # 要读取的文件的绝对路径
    "offset": int | None,   # The line number to start reading from
                            # 开始读取的行号
    "limit": int | None     # The number of lines to read
                            # 要读取的行数
}
```

**Output:**
**输出：**

```python
{
    "content": str,         # File contents with line numbers
                            # 带行号的文件内容
    "total_lines": int,     # Total number of lines in file
                            # 文件中的总行数
    "lines_returned": int   # Lines actually returned
                            # 实际返回的行数
}
```

### Write

**Input:**
**输入：**

```python
{
    "file_path": str,  # The absolute path to the file to write
                       # 要写入的文件的绝对路径
    "content": str     # The content to write to the file
                       # 要写入文件的内容
}
```

### Edit

**Input:**
**输入：**

```python
{
    "file_path": str,           # The absolute path to the file to modify
                                # 要修改的文件的绝对路径
    "old_string": str,          # The text to replace
                                # 要替换的文本
    "new_string": str,          # The text to replace it with
                                # 替换后的文本
    "replace_all": bool | None  # Replace all occurrences (default False)
                                # 替换所有出现（默认 False）
}
```

### Glob

**Input:**
**输入：**

```python
{
    "pattern": str,       # The glob pattern to match files against
                          # 用于匹配文件的 glob 模式
    "path": str | None    # The directory to search in (defaults to cwd)
                          # 要搜索的目录（默认为 cwd）
}
```

### Grep

**Input:**
**输入：**

```python
{
    "pattern": str,                    # The regular expression pattern
                                       # 正则表达式模式
    "path": str | None,                # File or directory to search in
                                       # 要搜索的文件或目录
    "glob": str | None,                # Glob pattern to filter files
                                       # 用于过滤文件的 glob 模式
    "output_mode": str | None,         # "content", "files_with_matches", or "count"
                                       # "content"、"files_with_matches" 或 "count"
    "-i": bool | None,                 # Case insensitive search
                                       # 不区分大小写搜索
    "-n": bool | None,                 # Show line numbers
                                       # 显示行号
}
```

## Example Usage
## 使用示例

### Basic file operations (using query)
### 基本文件操作（使用 query）

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ToolUseBlock
import asyncio

async def create_project():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode='acceptEdits',
        cwd="/home/user/project"
    )

    async for message in query(
        prompt="Create a Python project structure with setup.py",
        options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"Using tool: {block.name}")

asyncio.run(create_project())
```

### Error handling
### 错误处理

```python
from claude_agent_sdk import (
    query,
    CLINotFoundError,
    ProcessError,
    CLIJSONDecodeError
)

try:
    async for message in query(prompt="Hello"):
        print(message)
except CLINotFoundError:
    print("Please install Claude Code: npm install -g @anthropic-ai/claude-code")
    print("请安装 Claude Code: npm install -g @anthropic-ai/claude-code")
except ProcessError as e:
    print(f"Process failed with exit code: {e.exit_code}")
    print(f"进程失败，退出码: {e.exit_code}")
except CLIJSONDecodeError as e:
    print(f"Failed to parse response: {e}")
    print(f"解析响应失败: {e}")
```

### Using custom tools with ClaudeSDKClient
### 使用 ClaudeSDKClient 的自定义工具

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock
)
import asyncio
from typing import Any

# Define custom tools with @tool decorator
# 使用 @tool 装饰器定义自定义工具
@tool("calculate", "Perform mathematical calculations", {"expression": str})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = eval(args["expression"], {"__builtins__": {}})
        return {
            "content": [{
                "type": "text",
                "text": f"Result: {result}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "is_error": True
        }

async def main():
    # Create SDK MCP server with custom tools
    # 使用自定义工具创建 SDK MCP 服务器
    my_server = create_sdk_mcp_server(
        name="utilities",
        version="1.0.0",
        tools=[calculate]
    )

    # Configure options with the server
    # 使用服务器配置选项
    options = ClaudeAgentOptions(
        mcp_servers={"utils": my_server},
        allowed_tools=["mcp__utils__calculate"]
    )

    # Use ClaudeSDKClient for interactive tool usage
    # 使用 ClaudeSDKClient 进行交互式工具使用
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What's 123 * 456?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Calculation: {block.text}")

asyncio.run(main())
```

## See also
## 另请参阅

- [SDK overview](/docs/en/agent-sdk/overview) - General SDK concepts
- [SDK 概述](/docs/en/agent-sdk/overview) - 通用 SDK 概念
- [TypeScript SDK reference](/docs/en/agent-sdk/typescript) - TypeScript SDK documentation
- [TypeScript SDK 参考](/docs/en/agent-sdk/typescript) - TypeScript SDK 文档
- [CLI reference](https://code.claude.com/docs/en/cli-reference) - Command-line interface
- [CLI 参考](https://code.claude.com/docs/en/cli-reference) - 命令行接口
- [Common workflows](https://code.claude.com/docs/en/common-workflows) - Step-by-step guides
- [常见工作流程](https://code.claude.com/docs/en/common-workflows) - 分步指南
