"""
基本使用示例 - 展示 Skills Agent 的核心功能

这个示例展示了：
1. 如何创建 SkillsAgent 实例
2. 如何发送请求
3. 如何处理不同类型的消息

运行方式:
    uv run python examples/basic_usage.py

确保已配置认证（.env 文件或环境变量）:
    # 方式1: Anthropic API
    export ANTHROPIC_API_KEY=your-api-key

    # 方式2: 第三方代理（推荐）
    export ANTHROPIC_AUTH_TOKEN=your-token
    export ANTHROPIC_BASE_URL=https://your-proxy.com
"""

import asyncio
import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ResultMessage
from rich.console import Console
from rich.panel import Panel

from skills_agent.agent import SkillsAgent

console = Console()


async def main():
    """基本使用演示"""

    # 检查 API Key 或 Auth Token
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_auth_token = bool(os.environ.get("ANTHROPIC_AUTH_TOKEN"))
    if not (has_api_key or has_auth_token):
        console.print("[red]请设置 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN 环境变量[/red]")
        return

    console.print(Panel(
        "[bold cyan]Skills Agent 基本使用示例[/bold cyan]\n\n"
        "这个示例会请求 Claude 列出所有可用的 Skills。\n"
        "Claude 会自动发现 ~/.claude/skills/ 目录下的所有 Skills。",
        title="示例"
    ))
    console.print()

    # 创建 Agent 实例
    # 核心配置已经在 SkillsAgent 内部设置好了：
    # - setting_sources=["user", "project"]  # 启用 Skills 发现
    # - allowed_tools 包含 "Skill"  # 允许触发 Skills
    agent = SkillsAgent()

    # 发送请求
    prompt = "请列出系统中所有可用的 Skills，并简要说明每个 Skill 的功能。"

    console.print(f"[bold green]请求:[/bold green] {prompt}")
    console.print()

    # 处理响应
    async for message in agent.run(prompt):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    console.print(block.text)
                elif isinstance(block, ToolUseBlock):
                    console.print(f"[dim]🔧 调用工具: {block.name}[/dim]")

        elif isinstance(message, ResultMessage):
            console.print()
            console.print(Panel(
                f"[green]完成![/green]\n"
                f"耗时: {message.duration_ms}ms\n"
                f"轮数: {message.num_turns}",
                title="执行结果"
            ))


if __name__ == "__main__":
    asyncio.run(main())
