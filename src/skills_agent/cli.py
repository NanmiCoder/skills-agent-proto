"""
Skills Agent CLI - 命令行入口

支持两种模式：
1. 单次执行: skills-agent "你的请求"
2. 交互式对话: skills-agent --interactive

环境变量配置（通过 .env 文件）：
- ANTHROPIC_API_KEY: API 密钥
- ANTHROPIC_BASE_URL: 自定义 API 端点
- CLAUDE_MODEL: 使用的模型
- MAX_TURNS: 最大对话轮数
- PERMISSION_MODE: 权限模式

示例:
    # 单次执行
    uv run skills-agent "列出所有可用的 Skills"

    # 提取公众号文章
    uv run skills-agent "提取这篇文章: https://mp.weixin.qq.com/s/xxx"

    # 交互式对话
    uv run skills-agent --interactive
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

# 加载 .env 文件（在导入 agent 之前）
load_dotenv()

from skills_agent.agent import SkillsAgent

console = Console()


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        [bold cyan]Skills Agent[/bold cyan] - 能够使用 Skills 的 Coding Agent     ║
║                                                              ║
║   基于 Claude Agent SDK 构建                                  ║
║   自动发现和使用 ~/.claude/skills/ 中的 Skills                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    console.print(banner)


async def run_single(prompt: str) -> None:
    """单次执行模式"""
    agent = SkillsAgent()
    await agent.run_with_output(prompt)


async def run_interactive() -> None:
    """交互式对话模式"""
    print_banner()

    agent = SkillsAgent()

    console.print("[dim]输入 'exit' 或 'quit' 退出，'clear' 清屏[/dim]")
    console.print()

    while True:
        try:
            # 获取用户输入
            user_input = Prompt.ask("[bold green]你[/bold green]")

            # 处理特殊命令
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[yellow]再见！[/yellow]")
                break
            elif user_input.lower() == "clear":
                console.clear()
                print_banner()
                continue
            elif not user_input.strip():
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


def main():
    """主入口函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Skills Agent - 能够使用 Skills 的 Coding Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  skills-agent "列出所有可用的 Skills"
  skills-agent "提取这篇文章: https://mp.weixin.qq.com/s/xxx"
  skills-agent --interactive
        """
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="要执行的请求（如果不提供则进入交互模式）"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="进入交互式对话模式"
    )
    parser.add_argument(
        "--cwd",
        help="设置工作目录"
    )

    args = parser.parse_args()

    # 检查认证配置
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_auth_token = bool(os.environ.get("ANTHROPIC_AUTH_TOKEN"))  # 支持第三方代理
    use_bedrock = os.environ.get("CLAUDE_CODE_USE_BEDROCK") == "1"
    use_vertex = os.environ.get("CLAUDE_CODE_USE_VERTEX") == "1"
    use_foundry = os.environ.get("CLAUDE_CODE_USE_FOUNDRY") == "1"

    if not (has_api_key or has_auth_token or use_bedrock or use_vertex or use_foundry):
        console.print(Panel(
            "[red]未配置认证方式[/red]\n\n"
            "请选择以下任一方式配置：\n\n"
            "[yellow]方式1: Anthropic API[/yellow]\n"
            "  [green]export ANTHROPIC_API_KEY=your-api-key[/green]\n\n"
            "[yellow]方式2: 第三方代理 (推荐)[/yellow]\n"
            "  [green]export ANTHROPIC_AUTH_TOKEN=your-token[/green]\n"
            "  [green]export ANTHROPIC_BASE_URL=https://your-proxy.com[/green]\n\n"
            "[yellow]方式3: Amazon Bedrock[/yellow]\n"
            "  [green]export CLAUDE_CODE_USE_BEDROCK=1[/green]\n"
            "  并配置 AWS 凭证\n\n"
            "[yellow]方式4: Google Vertex AI[/yellow]\n"
            "  [green]export CLAUDE_CODE_USE_VERTEX=1[/green]\n"
            "  并配置 Google Cloud 凭证\n\n"
            "[dim]提示: 可以创建 .env 文件来配置，参考 .env.example[/dim]",
            title="认证错误",
            box=box.ROUNDED
        ))
        sys.exit(1)

    # 运行
    if args.interactive or not args.prompt:
        asyncio.run(run_interactive())
    else:
        asyncio.run(run_single(args.prompt))


if __name__ == "__main__":
    main()
