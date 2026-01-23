"""
LangChain Skills Agent CLI

命令行入口，提供演示和交互功能：
- 列出发现的 Skills
- 显示 system prompt（演示 Level 1）
- 执行用户请求（支持流式输出和 thinking 显示）
- 交互式对话模式

流式输出特性：
- 🧠 Thinking 面板：实时显示模型思考过程（蓝色）
- 🔧 Tool Calls：显示工具调用（黄色）
- 💬 Response 面板：逐字显示最终响应（绿色）
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.spinner import Spinner
from rich.layout import Layout
from rich.syntax import Syntax
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from .agent import LangChainSkillsAgent, check_api_credentials
from .skill_loader import SkillLoader
from .stream import ToolResultFormatter, has_args, DisplayLimits


# 加载环境变量（override=True 确保 .env 文件覆盖系统环境变量）
load_dotenv(override=True)

console = Console()

# 全局工具结果格式化器
formatter = ToolResultFormatter()


# === 流式处理状态 ===

class StreamState:
    """流式处理状态容器"""

    def __init__(self):
        self.thinking_text = ""
        self.response_text = ""
        self.tool_calls = []
        self.tool_results = []
        self.is_thinking = False
        self.is_responding = False
        self.is_processing = False  # 工具执行后等待 AI 继续处理

    def handle_event(self, event: dict) -> str:
        """
        处理单个流式事件，更新内部状态

        Args:
            event: 流式事件字典

        Returns:
            事件类型
        """
        event_type = event.get("type")

        if event_type == "thinking":
            self.is_thinking = True
            self.is_responding = False
            self.is_processing = False  # 收到新内容，不再是处理中
            self.thinking_text += event.get("content", "")

        elif event_type == "text":
            self.is_thinking = False
            self.is_responding = True
            self.is_processing = False  # 收到新内容，不再是处理中
            self.response_text += event.get("content", "")

        elif event_type == "tool_call":
            self.is_thinking = False
            self.is_responding = False
            self.is_processing = False
            self.tool_calls.append({
                "name": event.get("name", "unknown"),
                "args": event.get("args", {}),
            })

        elif event_type == "tool_result":
            self.is_processing = True  # 工具执行完成，等待 AI 继续处理
            self.tool_results.append({
                "name": event.get("name", "unknown"),
                "content": event.get("content", ""),
            })

        elif event_type == "done":
            self.is_processing = False
            if not self.response_text:
                self.response_text = event.get("response", "")

        return event_type

    def get_display_args(self) -> dict:
        """获取用于 create_streaming_display 的参数"""
        return {
            "thinking_text": self.thinking_text,
            "response_text": self.response_text,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "is_thinking": self.is_thinking,
            "is_responding": self.is_responding,
            "is_processing": self.is_processing,
        }


def display_final_results(
    state: StreamState,
    thinking_max_length: int = DisplayLimits.THINKING_FINAL,
    tool_result_max_length: int = DisplayLimits.TOOL_RESULT_FINAL,
    args_max_length: int = DisplayLimits.ARGS_FORMATTED,
    show_thinking: bool = True,
    show_response_panel: bool = True,
):
    """
    显示最终结果（非流式）

    Args:
        state: 流式处理状态
        thinking_max_length: thinking 最大显示长度
        tool_result_max_length: 工具结果最大显示长度
        args_max_length: 参数最大显示长度
        show_thinking: 是否显示 thinking
        show_response_panel: 是否用 Panel 显示响应
    """
    # 显示 thinking
    if show_thinking and state.thinking_text:
        display_thinking = state.thinking_text
        if len(display_thinking) > thinking_max_length:
            half = thinking_max_length // 2
            display_thinking = display_thinking[:half] + "\n\n... (truncated) ...\n\n" + display_thinking[-half:]
        console.print(Panel(
            Text(display_thinking, style="dim"),
            title="🧠 Thinking",
            border_style="blue",
        ))

    # 显示工具调用和结果
    if state.tool_calls:
        for i, tc in enumerate(state.tool_calls):
            console.print(f"[yellow]🔧 Tool: {tc['name']}[/yellow]")
            if has_args(tc.get("args")):
                for elem in format_tool_args(tc["args"], max_length=args_max_length):
                    console.print(elem)
            # 显示对应的工具结果
            if i < len(state.tool_results):
                tr = state.tool_results[i]
                result_elements = format_tool_result(
                    tr['name'],
                    tr.get('content', ''),
                    max_length=tool_result_max_length,
                )
                for elem in result_elements:
                    console.print(elem)
        console.print()

    # 显示最终响应
    if state.response_text:
        if show_response_panel:
            console.print(Panel(
                Markdown(state.response_text),
                title="💬 Response",
                border_style="green",
            ))
        else:
            console.print(f"\n[bold blue]Assistant:[/bold blue]")
            console.print(Markdown(state.response_text))
            console.print()


def format_tool_result(name: str, content: str, max_length: int = 800) -> list:
    """
    智能格式化工具结果

    使用 ToolResultFormatter 进行统一格式化。

    Args:
        name: 工具名称
        content: 工具输出内容
        max_length: 最大显示长度

    Returns:
        Rich 可渲染元素列表
    """
    result = formatter.format(name, content, max_length)
    return result.elements


def format_tool_args(args: dict, max_length: int = 300) -> list:
    """
    格式化工具参数显示

    Args:
        args: 工具参数字典
        max_length: 最大显示长度

    Returns:
        Rich 可渲染元素列表
    """
    elements = []
    try:
        args_formatted = json.dumps(args, indent=2, ensure_ascii=False)
        if len(args_formatted) > max_length:
            args_formatted = args_formatted[:max_length] + "\n..."
        elements.append(Syntax(args_formatted, "json", theme="monokai", line_numbers=False))
    except (TypeError, ValueError):
        args_str = str(args)
        if len(args_str) > max_length:
            args_str = args_str[:max_length] + "..."
        elements.append(Text(f"   {args_str}", style="dim"))
    return elements


def create_streaming_display(
    thinking_text: str = "",
    response_text: str = "",
    tool_calls: list = None,
    tool_results: list = None,
    is_thinking: bool = False,
    is_responding: bool = False,
    is_waiting: bool = False,
    is_processing: bool = False,
) -> Group:
    """
    创建流式显示的布局

    Args:
        thinking_text: 当前累积的 thinking 文本
        response_text: 当前累积的响应文本
        tool_calls: 工具调用列表
        tool_results: 工具结果列表
        is_thinking: 是否正在思考
        is_responding: 是否正在响应
        is_waiting: 是否处于初始等待状态
        is_processing: 工具执行后等待 AI 继续处理

    Returns:
        Rich Group 对象
    """
    elements = []
    tool_calls = tool_calls or []
    tool_results = tool_results or []

    # 判断是否有工具正在执行中
    is_tool_executing = len(tool_calls) > len(tool_results)

    # 初始等待状态 - 显示 spinner 提示
    if is_waiting and not thinking_text and not response_text and not tool_calls:
        spinner = Spinner("dots", text=" AI 正在思考中...", style="cyan")
        elements.append(spinner)
        return Group(*elements)

    # Thinking 面板
    if thinking_text:
        thinking_title = "🧠 Thinking"
        if is_thinking:
            thinking_title += " ..."
        # 限制显示长度，保留最新内容
        display_thinking = thinking_text
        if len(display_thinking) > DisplayLimits.THINKING_STREAM:
            display_thinking = "..." + display_thinking[-DisplayLimits.THINKING_STREAM:]
        elements.append(Panel(
            Text(display_thinking, style="dim"),
            title=thinking_title,
            border_style="blue",
            padding=(0, 1),
        ))

    # Tool Calls 和 Results 配对显示
    if tool_calls:
        for i, tc in enumerate(tool_calls):
            # 显示工具调用
            tool_text = f"🔧 {tc['name']}"
            if has_args(tc.get("args")):
                # 简化显示参数
                args_str = str(tc["args"])
                if len(args_str) > DisplayLimits.ARGS_INLINE:
                    args_str = args_str[:DisplayLimits.ARGS_INLINE] + "..."
                tool_text += f"\n   {args_str}"
            elements.append(Text(tool_text, style="yellow"))

            # 显示对应的结果或"正在执行"状态
            if i < len(tool_results):
                # 已有结果，显示结果
                tr = tool_results[i]
                result_elements = format_tool_result(
                    tr['name'],
                    tr.get('content', ''),
                    max_length=DisplayLimits.TOOL_RESULT_STREAM,
                )
                elements.extend(result_elements)
            else:
                # 还没有结果，显示带 spinner 的"正在执行"状态
                spinner = Spinner("dots", text=f" {tc['name']} 正在执行中...", style="yellow")
                elements.append(spinner)

    # 工具执行后等待 AI 继续处理的状态
    if is_processing and not is_thinking and not is_responding and not response_text:
        spinner = Spinner("dots", text=" AI 正在分析结果...", style="cyan")
        elements.append(spinner)

    # Response 面板
    if response_text:
        response_title = "💬 Response"
        if is_responding:
            response_title += " ..."
        elements.append(Panel(
            Markdown(response_text),
            title=response_title,
            border_style="green",
            padding=(0, 1),
        ))
    elif is_responding and not thinking_text:
        # 显示等待指示器
        elements.append(Text("⏳ Generating response...", style="dim"))

    return Group(*elements) if elements else Text("⏳ Processing...", style="dim")


def print_banner():
    """打印欢迎横幅"""
    banner = """
[bold cyan]LangChain Skills Agent[/bold cyan]
[dim]演示 Skills 三层加载机制的底层原理[/dim]

[yellow]Level 1[/yellow]: 启动时 → Skills 元数据注入 system prompt
[yellow]Level 2[/yellow]: 请求匹配时 → load_skill 加载详细指令
[yellow]Level 3[/yellow]: 执行时 → bash 运行脚本，仅输出进入上下文
"""
    console.print(Panel(banner, title="Skills Agent Demo", border_style="cyan"))


def cmd_list_skills():
    """列出发现的 Skills"""
    console.print("\n[bold cyan]Discovering Skills...[/bold cyan]\n")

    loader = SkillLoader()
    skills = loader.scan_skills()

    if not skills:
        console.print("[yellow]No skills found.[/yellow]")
        console.print("Skills are loaded from:")
        console.print("  - ~/.claude/skills/")
        console.print("  - .claude/skills/")
        return

    table = Table(title=f"Found {len(skills)} Skills")
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")
    table.add_column("Path", style="dim")

    for skill in skills:
        # 截断描述
        desc = skill.description
        if len(desc) > 60:
            desc = desc[:57] + "..."

        table.add_row(
            skill.name,
            desc,
            str(skill.skill_path.relative_to(skill.skill_path.parent.parent)),
        )

    console.print(table)


def cmd_show_prompt():
    """显示 system prompt（演示 Level 1）"""
    console.print("\n[bold cyan]Building System Prompt (Level 1)...[/bold cyan]\n")

    agent = LangChainSkillsAgent()
    prompt = agent.get_system_prompt()

    console.print(Panel(
        Markdown(prompt),
        title="System Prompt",
        subtitle="Skills metadata injected here",
        border_style="green",
    ))

    # 统计信息
    skills = agent.get_discovered_skills()
    token_estimate = len(prompt) // 4  # 粗略估算

    console.print(f"\n[dim]Skills discovered: {len(skills)}[/dim]")
    console.print(f"[dim]Estimated tokens: ~{token_estimate}[/dim]")


def cmd_run(prompt: str, enable_thinking: bool = True):
    """
    执行单次请求，支持流式输出和 thinking 显示

    Args:
        prompt: 用户请求
        enable_thinking: 是否启用 thinking 显示
    """
    console.print(Panel(f"[bold cyan]User Request:[/bold cyan]\n{prompt}"))
    console.print()

    # 检查 API 认证（支持 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN）
    if not check_api_credentials():
        console.print("[red]Error: API credentials not set[/red]")
        console.print("Please set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN in .env file")
        sys.exit(1)

    agent = LangChainSkillsAgent(enable_thinking=enable_thinking)

    console.print("[dim]Running agent with streaming output...[/dim]\n")

    try:
        state = StreamState()

        with Live(console=console, refresh_per_second=10, transient=True) as live:
            # 立即显示等待状态
            live.update(create_streaming_display(is_waiting=True))

            for event in agent.stream_events(prompt):
                event_type = state.handle_event(event)

                # 更新 Live 显示
                live.update(create_streaming_display(**state.get_display_args()))

                # tool_call 和 tool_result 时强制刷新
                # tool_call: 确保"正在执行"状态立即可见
                # tool_result: 确保"正在分析结果"状态立即可见
                if event_type in ("tool_call", "tool_result"):
                    live.refresh()

        # 显示最终结果
        console.print()
        display_final_results(
            state,
            tool_result_max_length=1000,  # cmd_run 用较长的限制
            args_max_length=400,
            show_response_panel=True,
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


def cmd_interactive(enable_thinking: bool = True):
    """
    交互式对话模式，支持流式输出和 thinking 显示

    Args:
        enable_thinking: 是否启用 thinking 显示
    """
    print_banner()

    # 检查 API 认证（支持 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN）
    if not check_api_credentials():
        console.print("[red]Error: API credentials not set[/red]")
        console.print("Please set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN in .env file")
        sys.exit(1)

    agent = LangChainSkillsAgent(enable_thinking=enable_thinking)

    # 显示发现的 Skills
    skills = agent.get_discovered_skills()
    console.print(f"\n[green]✓[/green] Discovered {len(skills)} skills")
    for skill in skills:
        console.print(f"  - {skill['name']}")
    console.print()

    thinking_status = "[green]enabled[/green]" if enable_thinking else "[dim]disabled[/dim]"
    console.print(f"[dim]Extended Thinking: {thinking_status}[/dim]")
    console.print("[dim]Commands: 'exit' to quit, 'skills' to list skills, 'prompt' to show system prompt[/dim]\n")

    thread_id = "interactive"

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()

            if not user_input:
                continue

            # 特殊命令
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[dim]Goodbye![/dim]")
                break

            if user_input.lower() == "skills":
                cmd_list_skills()
                continue

            if user_input.lower() == "prompt":
                cmd_show_prompt()
                continue

            # 运行 agent（流式输出）
            console.print()

            state = StreamState()

            with Live(console=console, refresh_per_second=10, transient=True) as live:
                # 立即显示等待状态
                live.update(create_streaming_display(is_waiting=True))

                for event in agent.stream_events(user_input, thread_id=thread_id):
                    event_type = state.handle_event(event)

                    # 更新 Live 显示
                    live.update(create_streaming_display(**state.get_display_args()))

                    # tool_call 和 tool_result 时强制刷新
                    # tool_call: 确保"正在执行"状态立即可见
                    # tool_result: 确保"正在分析结果"状态立即可见
                    if event_type in ("tool_call", "tool_result"):
                        live.refresh()

            # 显示最终结果（交互模式：简化显示，不用 Panel 包裹响应）
            display_final_results(
                state,
                thinking_max_length=500,  # 交互模式用较短的 thinking 显示
                tool_result_max_length=DisplayLimits.TOOL_RESULT_FINAL,
                args_max_length=DisplayLimits.ARGS_FORMATTED,
                show_response_panel=False,  # 交互模式不用 Panel
            )

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        description="LangChain Skills Agent - 演示 Skills 三层加载机制（支持流式输出和 Extended Thinking）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 列出发现的 Skills
  %(prog)s --list-skills

  # 显示 system prompt（演示 Level 1）
  %(prog)s --show-prompt

  # 执行请求（默认启用 thinking）
  %(prog)s "提取这篇公众号文章: https://mp.weixin.qq.com/s/xxx"

  # 执行请求（禁用 thinking）
  %(prog)s --no-thinking "列出当前目录的文件"

  # 交互式模式
  %(prog)s --interactive

Features:
  - 🧠 Extended Thinking: 显示模型的思考过程（蓝色面板）
  - 🔧 Tool Calls: 显示工具调用（黄色）
  - 💬 Streaming Response: 逐字显示响应（绿色面板）
""",
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        help="要执行的请求",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="进入交互式对话模式",
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="列出发现的 Skills",
    )
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="显示 system prompt（演示 Level 1）",
    )
    parser.add_argument(
        "--no-thinking",
        action="store_true",
        help="禁用 Extended Thinking（可降低延迟和成本）",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        help="设置工作目录",
    )

    args = parser.parse_args()

    # 设置工作目录
    if args.cwd:
        os.chdir(args.cwd)

    # thinking 开关
    enable_thinking = not args.no_thinking

    # 执行命令
    if args.list_skills:
        cmd_list_skills()
    elif args.show_prompt:
        cmd_show_prompt()
    elif args.interactive:
        cmd_interactive(enable_thinking=enable_thinking)
    elif args.prompt:
        cmd_run(args.prompt, enable_thinking=enable_thinking)
    else:
        # 默认进入交互模式
        cmd_interactive(enable_thinking=enable_thinking)


if __name__ == "__main__":
    main()
