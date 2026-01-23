"""
基本使用示例 - 展示 LangChain Skills Agent 的核心功能

这个示例展示了：
1. 如何创建 LangChainSkillsAgent 实例
2. 如何发送请求
3. 如何获取响应

运行方式:
    uv run python examples/basic_usage.py

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

from langchain_skills import LangChainSkillsAgent

console = Console()


def main():
    """基本使用演示"""

    console.print(Panel(
        "[bold cyan]LangChain Skills Agent 基本使用示例[/bold cyan]\n\n"
        "这个示例会请求 Agent 列出所有可用的 Skills。\n"
        "Agent 会自动发现 ~/.claude/skills/ 目录下的所有 Skills。",
        title="示例"
    ))
    console.print()

    # 创建 Agent 实例
    agent = LangChainSkillsAgent()

    # 显示发现的 Skills
    skills = agent.get_discovered_skills()
    console.print(f"[dim]发现 {len(skills)} 个 Skills[/dim]")
    for skill in skills:
        console.print(f"  - {skill['name']}: {skill['description'][:50]}...")
    console.print()

    # 发送请求
    prompt = "请列出系统中所有可用的 Skills，并简要说明每个 Skill 的功能。"

    console.print(f"[bold green]请求:[/bold green] {prompt}")
    console.print()

    try:
        # 运行 Agent
        result = agent.invoke(prompt)
        response = agent.get_last_response(result)

        console.print("[bold blue]响应:[/bold blue]")
        console.print(response)

        console.print()
        console.print(Panel(
            "[green]完成![/green]",
            title="执行结果"
        ))

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        console.print("[yellow]提示: 请确保已正确配置 ANTHROPIC_API_KEY[/yellow]")


if __name__ == "__main__":
    main()
