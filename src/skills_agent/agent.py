"""
Skills Agent - 能够发现和使用 Skills 的 Coding Agent

核心配置说明：
- setting_sources: 启用 Skills 发现
  - "user": 加载 ~/.claude/skills/ 目录下的 Skills
  - "project": 加载 .claude/skills/ 目录下的 Skills
- allowed_tools: 必须包含 "Skill" 工具，否则无法触发任何 Skill

Skills 三层加载机制（由 Claude 自动完成）：
- Level 1: 启动时加载所有 Skills 的元数据（name, description）到 system prompt
- Level 2: 用户请求匹配 Skill 描述时，Claude 读取 SKILL.md 获取详细指令
- Level 3: 按指令执行脚本，脚本代码不进入上下文，只有输出进入上下文

环境变量配置（可选）：
- ANTHROPIC_API_KEY: API 密钥（必填）
- ANTHROPIC_BASE_URL: 自定义 API 端点
- CLAUDE_MODEL: 使用的模型名称
- MAX_TURNS: 最大对话轮数
- PERMISSION_MODE: 权限模式
"""

import os
from typing import AsyncIterator, Optional
from pathlib import Path

from dotenv import load_dotenv
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
)
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown

# 加载 .env 文件
load_dotenv()

# 类型别名
Message = AssistantMessage | ResultMessage


def get_config():
    """从环境变量获取配置"""
    return {
        "model": os.getenv("CLAUDE_MODEL"),
        "max_turns": int(os.getenv("MAX_TURNS")) if os.getenv("MAX_TURNS") else None,
        "permission_mode": os.getenv("PERMISSION_MODE", "acceptEdits"),
    }


class SkillsAgent:
    """
    能够使用 Skills 的 Coding Agent

    通过配置 Claude Agent SDK 的 setting_sources 和 allowed_tools，
    让 Claude 能够自动发现和使用 Skills。

    使用示例:
    ```python
    agent = SkillsAgent()

    async for message in agent.run("提取这篇公众号文章"):
        print(message)
    ```
    """

    def __init__(
        self,
        cwd: Optional[str | Path] = None,
        permission_mode: Optional[str] = None,
        max_turns: Optional[int] = None,
        model: Optional[str] = None,
    ):
        """
        初始化 Skills Agent

        所有参数都可以通过环境变量配置，参数优先级高于环境变量。

        Args:
            cwd: 工作目录，默认为当前目录
            permission_mode: 权限模式（环境变量: PERMISSION_MODE）
                - "default": 标准权限行为
                - "acceptEdits": 自动接受文件编辑（推荐用于自动化）
                - "bypassPermissions": 绕过所有权限检查（谨慎使用）
            max_turns: 最大对话轮数限制（环境变量: MAX_TURNS）
            model: 使用的模型（环境变量: CLAUDE_MODEL）
        """
        self.console = Console()
        self.cwd = str(cwd) if cwd else None

        # 从环境变量获取默认配置
        env_config = get_config()

        # 参数优先级高于环境变量
        _permission_mode = permission_mode or env_config["permission_mode"]
        _max_turns = max_turns or env_config["max_turns"]
        _model = model or env_config["model"]

        # 核心配置：这是让 Agent 能使用 Skills 的关键！
        self.options = ClaudeAgentOptions(
            # 关键配置 1：启用 Skills 发现
            # "user" = ~/.claude/skills/
            # "project" = .claude/skills/
            setting_sources=["user", "project"],

            # 关键配置 2：允许使用的工具列表，必须包含 "Skill"
            allowed_tools=[
                "Skill",    # 触发 Skills 的核心工具
                "Read",     # 读取文件
                "Write",    # 写入文件
                "Edit",     # 编辑文件
                "Bash",     # 执行命令
                "Glob",     # 查找文件
                "Grep",     # 搜索内容
            ],

            # 权限模式
            permission_mode=_permission_mode,

            # 工作目录
            cwd=self.cwd,

            # 最大轮数
            max_turns=_max_turns,

            # 模型选择
            model=_model,
        )

    async def run(self, prompt: str) -> AsyncIterator[Message]:
        """
        运行 Agent 处理用户请求

        Claude 会自动：
        1. 根据 system prompt 中的 Skills 元数据判断是否需要触发 Skill
        2. 如果匹配，读取对应 SKILL.md 获取详细指令
        3. 按指令执行脚本或其他操作

        Args:
            prompt: 用户请求

        Yields:
            Message: Claude 返回的消息
        """
        async for message in query(prompt=prompt, options=self.options):
            yield message

    async def run_with_output(self, prompt: str) -> None:
        """
        运行 Agent 并将结果输出到控制台（使用 rich 美化）

        Args:
            prompt: 用户请求
        """
        self.console.print(Panel(f"[bold cyan]用户请求:[/bold cyan]\n{prompt}"))
        self.console.print()

        async for message in self.run(prompt):
            self._handle_message(message)

    def _handle_message(self, message: Message) -> None:
        """处理并显示消息"""
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    # 使用 Markdown 渲染文本
                    self.console.print(Markdown(block.text))
                elif isinstance(block, ToolUseBlock):
                    self.console.print(
                        f"[dim]🔧 调用工具: [cyan]{block.name}[/cyan][/dim]"
                    )
                elif isinstance(block, ToolResultBlock):
                    # 工具结果通常很长，只显示摘要
                    content = str(block.content)[:200] if block.content else ""
                    if len(str(block.content or "")) > 200:
                        content += "..."
                    self.console.print(f"[dim]   结果: {content}[/dim]")

        elif isinstance(message, ResultMessage):
            self.console.print()
            self.console.print(
                Panel(
                    f"[green]完成![/green]\n"
                    f"耗时: {message.duration_ms}ms | "
                    f"轮数: {message.num_turns} | "
                    f"费用: ${message.total_cost_usd:.4f}" if message.total_cost_usd else "",
                    title="执行结果",
                )
            )
