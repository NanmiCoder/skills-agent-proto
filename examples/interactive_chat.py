"""
交互式对话示例 - 与 LangChain Skills Agent 进行多轮对话

这个示例展示了如何进行交互式对话，
让用户可以连续发送多个请求给 Agent。

运行方式:
    uv run python examples/interactive_chat.py

确保已配置认证（.env 文件或环境变量）:
    export ANTHROPIC_API_KEY=your-api-key
"""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

from langchain_skills import LangChainSkillsAgent

console = Console()


def print_banner():
    """打印欢迎横幅"""
    console.print(Panel(
        "[bold cyan]LangChain Skills Agent 交互式对话[/bold cyan]\n\n"
        "你可以与 Agent 进行多轮对话，Agent 能够：\n"
        "- 自动发现和使用 ~/.claude/skills/ 中的 Skills\n"
        "- 读取、编辑文件\n"
        "- 执行命令\n\n"
        "[dim]输入 'exit' 退出，'skills' 查看可用 Skills[/dim]",
        title="欢迎"
    ))
    console.print()


def chat():
    """交互式对话"""

    print_banner()

    # 创建 Agent
    agent = LangChainSkillsAgent()

    # 显示发现的 Skills
    skills = agent.get_discovered_skills()
    console.print(f"[dim]已加载 {len(skills)} 个 Skills[/dim]")
    console.print()

    while True:
        try:
            # 获取用户输入
            user_input = Prompt.ask("[bold green]你[/bold green]")

            # 处理特殊命令
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[yellow]再见！[/yellow]")
                break

            if user_input.lower() == "skills":
                console.print("\n[bold]可用 Skills:[/bold]")
                for skill in skills:
                    console.print(f"  - [green]{skill['name']}[/green]: {skill['description'][:60]}...")
                console.print()
                continue

            if not user_input.strip():
                continue

            # 运行 Agent
            console.print()
            try:
                result = agent.invoke(user_input)
                response = agent.get_last_response(result)
                console.print("[bold blue]Agent:[/bold blue]")
                console.print(Markdown(response))
            except Exception as e:
                console.print(f"[red]错误: {e}[/red]")

            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]中断，退出...[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")


def main():
    """主入口"""
    chat()


if __name__ == "__main__":
    main()
