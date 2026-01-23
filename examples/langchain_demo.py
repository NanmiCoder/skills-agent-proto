#!/usr/bin/env python3
"""
LangChain Skills Agent 演示脚本

演示 Skills 三层加载机制的底层原理，适合自媒体视频教学。

运行方式：
    # 安装依赖
    uv sync

    # 运行演示
    uv run examples/langchain_demo.py

演示内容：
    1. Level 1: Skills 发现和 system prompt 注入
    2. Level 2: load_skill 工具加载详细指令
    3. Level 3: bash 执行脚本（仅输出进入上下文）
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import print as rprint

from langchain_skills import SkillLoader, discover_skills, get_skill_content


console = Console()


def demo_level1():
    """
    演示 Level 1: Skills 发现

    启动时自动扫描 Skills 目录，解析 YAML frontmatter，
    将元数据（name + description）注入 system prompt。

    Token 消耗：约 100 tokens/skill
    """
    console.print(Panel(
        "[bold yellow]Level 1: Skills 发现[/bold yellow]\n\n"
        "启动时扫描目录，解析 YAML frontmatter，\n"
        "将元数据注入 system prompt",
        border_style="yellow"
    ))

    # 创建 SkillLoader
    loader = SkillLoader()

    console.print("\n[dim]扫描目录:[/dim]")
    console.print("  - ~/.claude/skills/")
    console.print("  - .claude/skills/")
    console.print()

    # 扫描 Skills
    skills = loader.scan_skills()

    if not skills:
        console.print("[yellow]未发现任何 Skills[/yellow]")
        return

    # 显示发现的 Skills
    table = Table(title=f"发现 {len(skills)} 个 Skills")
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")
    table.add_column("~Tokens", justify="right", style="cyan")

    for skill in skills:
        # 估算 tokens（每个 skill 约 100 tokens）
        desc = skill.description[:50] + "..." if len(skill.description) > 50 else skill.description
        tokens = len(skill.to_prompt_line()) // 4
        table.add_row(skill.name, desc, f"~{tokens}")

    console.print(table)

    # 显示生成的 system prompt 片段
    console.print("\n[bold]注入到 system prompt 的内容:[/bold]\n")
    prompt = loader.build_system_prompt()

    # 只显示 Skills 部分
    lines = prompt.split("\n")
    skills_section = []
    in_skills = False
    for line in lines:
        if "Available Skills" in line:
            in_skills = True
        if in_skills:
            skills_section.append(line)
            if line.startswith("**Important**"):
                break

    console.print(Panel(
        "\n".join(skills_section),
        title="System Prompt (Skills Section)",
        border_style="green"
    ))


def demo_level2():
    """
    演示 Level 2: 加载 Skill 详细指令

    当用户请求匹配 Skill 描述时，
    LLM 调用 load_skill 工具读取 SKILL.md 完整内容。

    Token 消耗：约 5k tokens
    """
    console.print(Panel(
        "[bold yellow]Level 2: 加载详细指令[/bold yellow]\n\n"
        "用户请求匹配时，load_skill 工具\n"
        "读取 SKILL.md 完整内容返回给 LLM",
        border_style="yellow"
    ))

    # 发现 Skills
    skills = discover_skills()

    if not skills:
        console.print("[yellow]未发现任何 Skills，跳过此演示[/yellow]")
        return

    # 选择第一个 skill 演示
    skill_name = skills[0].name
    console.print(f"\n[dim]演示加载 Skill: {skill_name}[/dim]\n")

    # 加载 Skill 内容
    content = get_skill_content(skill_name)

    if content:
        # 显示指令预览
        preview = content.instructions[:500]
        if len(content.instructions) > 500:
            preview += "\n\n... (更多内容)"

        console.print(Panel(
            preview,
            title=f"SKILL.md 内容 (前 500 字符)",
            border_style="blue"
        ))

        # 统计信息
        token_estimate = len(content.instructions) // 4

        console.print(f"\n[dim]指令长度: {len(content.instructions)} 字符[/dim]")
        console.print(f"[dim]估算 tokens: ~{token_estimate}[/dim]")
        console.print(f"[dim]脚本发现: 由 LLM 从指令中自主发现[/dim]")


def demo_level3():
    """
    演示 Level 3: 脚本执行

    LLM 按照 Skill 指令调用 bash 工具执行脚本。
    脚本代码不进入上下文，只有输出进入。

    这是 Skills 高效的关键：大量代码被封装在脚本中，
    不占用上下文空间。
    """
    console.print(Panel(
        "[bold yellow]Level 3: 脚本执行[/bold yellow]\n\n"
        "bash 工具执行脚本，脚本代码不进入上下文，\n"
        "只有 stdout/stderr 输出返回给 LLM",
        border_style="yellow"
    ))

    console.print("\n[bold]工作流程:[/bold]\n")

    flow = """
    ┌─────────────────┐
    │  LLM 调用 bash  │
    │  tool 执行脚本  │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  subprocess     │
    │  执行 Python    │  ← 脚本代码不进入上下文
    │  脚本           │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  stdout/stderr  │  ← 只有输出进入上下文
    │  返回给 LLM     │
    └─────────────────┘
    """

    console.print(flow)

    console.print("\n[bold]优势:[/bold]")
    console.print("  - 脚本可以很长（数百行），不占用上下文")
    console.print("  - 复杂逻辑封装在脚本中，LLM 只需要调用")
    console.print("  - 脚本可以安装依赖、调用外部 API 等")


def demo_token_analysis():
    """
    Token 消耗分析
    """
    console.print(Panel(
        "[bold yellow]Token 消耗分析[/bold yellow]\n\n"
        "渐进式披露确保只加载必要内容",
        border_style="yellow"
    ))

    loader = SkillLoader()
    skills = loader.scan_skills()

    table = Table(title="三层加载机制 Token 消耗")
    table.add_column("Level", style="cyan")
    table.add_column("时机", style="white")
    table.add_column("内容", style="green")
    table.add_column("Token 估算", justify="right", style="yellow")

    # Level 1
    prompt = loader.build_system_prompt()
    level1_tokens = len(prompt) // 4
    table.add_row(
        "Level 1",
        "启动时",
        f"{len(skills)} 个 Skills 元数据",
        f"~{level1_tokens}"
    )

    # Level 2
    if skills:
        content = loader.load_skill(skills[0].name)
        if content:
            level2_tokens = len(content.instructions) // 4
            table.add_row(
                "Level 2",
                "请求匹配时",
                "SKILL.md 详细指令",
                f"~{level2_tokens}"
            )

    # Level 3
    table.add_row(
        "Level 3",
        "执行时",
        "脚本输出",
        "仅输出进入"
    )

    console.print(table)

    console.print("\n[bold green]关键洞察:[/bold green]")
    console.print("  - 可以安装大量 Skills 而不影响性能")
    console.print("  - 只在需要时加载详细指令")
    console.print("  - 脚本代码永不进入上下文")


def main():
    """主函数"""
    console.print(Panel(
        "[bold cyan]LangChain Skills Agent 演示[/bold cyan]\n\n"
        "演示 Skills 三层加载机制的底层原理\n"
        "适合自媒体视频教学",
        title="Skills Agent Demo",
        border_style="cyan"
    ))

    console.print("\n" + "=" * 60 + "\n")

    # Level 1 演示
    demo_level1()

    console.print("\n" + "=" * 60 + "\n")

    # Level 2 演示
    demo_level2()

    console.print("\n" + "=" * 60 + "\n")

    # Level 3 演示
    demo_level3()

    console.print("\n" + "=" * 60 + "\n")

    # Token 分析
    demo_token_analysis()

    console.print("\n" + "=" * 60 + "\n")

    console.print(Panel(
        "[bold green]演示完成![/bold green]\n\n"
        "现在可以尝试运行完整的 Agent:\n\n"
        "  uv run langchain-skills --list-skills\n"
        "  uv run langchain-skills --show-prompt\n"
        "  uv run langchain-skills --interactive",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
