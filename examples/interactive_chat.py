"""
交互式对话示例 - 与 Skills Agent 进行多轮对话

这个示例展示了如何进行交互式对话，
让用户可以连续发送多个请求给 Agent。

运行方式:
    uv run python examples/interactive_chat.py

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

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from skills_agent.agent import SkillsAgent

console = Console()


def print_banner():
    """打印欢迎横幅"""
    console.print(Panel(
        "[bold cyan]Skills Agent 交互式对话[/bold cyan]\n\n"
        "你可以与 Agent 进行多轮对话，Agent 能够：\n"
        "• 自动发现和使用 ~/.claude/skills/ 中的 Skills\n"
        "• 读取、编辑文件\n"
        "• 执行命令\n\n"
        "[dim]输入 'exit' 退出，'skills' 查看可用 Skills[/dim]",
        title="欢迎"
    ))
    console.print()


async def chat():
    """交互式对话"""

    # 检查 API Key 或 Auth Token
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_auth_token = bool(os.environ.get("ANTHROPIC_AUTH_TOKEN"))
    if not (has_api_key or has_auth_token):
        console.print("[red]请设置 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN 环境变量[/red]")
        return

    print_banner()

    # 创建 Agent
    agent = SkillsAgent()

    while True:
        try:
            # 获取用户输入
            user_input = Prompt.ask("[bold green]你[/bold green]")

            # 处理特殊命令
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[yellow]再见！[/yellow]")
                break

            if user_input.lower() == "skills":
                user_input = "请列出所有可用的 Skills 及其简要说明"

            if not user_input.strip():
                continue

            # 运行 Agent
            console.print()
            await agent.run_with_output(user_input)
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]中断，退出...[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            import traceback
            traceback.print_exc()


def main():
    """主入口"""
    asyncio.run(chat())


if __name__ == "__main__":
    main()
