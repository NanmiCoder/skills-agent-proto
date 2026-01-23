"""
文章提取示例 - 使用 news-extractor Skill 提取公众号文章

这个示例展示了 Skills 的完整工作流程：

1. Level 1 - 元数据加载（启动时）:
   Claude 在启动时自动加载 ~/.claude/skills/news-extractor/SKILL.md 的元数据
   （name 和 description），约 100 tokens

2. Level 2 - 指令加载（触发时）:
   当用户请求匹配 news-extractor 的描述时，Claude 读取 SKILL.md 的完整内容
   获取详细的操作指令

3. Level 3 - 脚本执行（按需）:
   Claude 按指令执行 scripts/extract_news.py 脚本
   脚本代码不进入上下文，只有输出结果进入上下文

运行方式:
    uv run python examples/extract_article.py

    # 或指定 URL
    uv run python examples/extract_article.py "https://mp.weixin.qq.com/s/xxx"

确保:
    1. 已配置认证（ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN）
    2. 已安装 news-extractor skill 到 ~/.claude/skills/news-extractor/
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
from rich.markdown import Markdown

from skills_agent.agent import SkillsAgent

console = Console()


async def extract_article(url: str):
    """使用 news-extractor Skill 提取文章"""

    console.print(Panel(
        "[bold cyan]文章提取示例[/bold cyan]\n\n"
        "这个示例演示 Skills 的三层加载机制：\n"
        "• Level 1: 元数据已在启动时加载到 system prompt\n"
        "• Level 2: Claude 会读取 SKILL.md 获取详细指令\n"
        "• Level 3: 执行 extract_news.py 脚本，只有输出进入上下文",
        title="Skills 工作流程演示"
    ))
    console.print()

    # 创建 Agent
    agent = SkillsAgent()

    # 构造请求
    # Claude 会根据 system prompt 中的 Skills 元数据，
    # 自动判断这个请求需要使用 news-extractor Skill
    prompt = f"""
请提取这篇文章的内容：
{url}

请输出：
1. JSON 格式到 ./output 目录
2. Markdown 格式到 ./output 目录
"""

    console.print(f"[bold green]请求:[/bold green]")
    console.print(Markdown(prompt))
    console.print()

    # 运行 Agent
    async for message in agent.run(prompt):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    console.print(Markdown(block.text))
                elif isinstance(block, ToolUseBlock):
                    # 显示工具调用，可以观察到 Claude 如何触发 Skill
                    if block.name == "Skill":
                        console.print(f"[bold yellow]🎯 触发 Skill: {block.input.get('skill', 'unknown')}[/bold yellow]")
                    else:
                        console.print(f"[dim]🔧 调用工具: {block.name}[/dim]")

        elif isinstance(message, ResultMessage):
            console.print()
            console.print(Panel(
                f"[green]提取完成![/green]\n"
                f"耗时: {message.duration_ms}ms\n"
                f"轮数: {message.num_turns}\n"
                f"费用: ${message.total_cost_usd:.4f}" if message.total_cost_usd else "",
                title="执行结果"
            ))


async def main():
    """主函数"""

    # 检查 API Key 或 Auth Token
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_auth_token = bool(os.environ.get("ANTHROPIC_AUTH_TOKEN"))
    if not (has_api_key or has_auth_token):
        console.print("[red]请设置 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN 环境变量[/red]")
        return

    # 获取 URL 参数
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # 使用示例 URL（你需要替换成真实的文章 URL）
        url = "https://mp.weixin.qq.com/s/example-article-id"
        console.print(f"[yellow]提示: 未提供 URL，使用示例 URL: {url}[/yellow]")
        console.print("[dim]使用方式: uv run python examples/extract_article.py \"真实的文章URL\"[/dim]")
        console.print()

    await extract_article(url)


if __name__ == "__main__":
    asyncio.run(main())
