"""
文章提取示例 - 使用 news-extractor Skill 提取公众号文章

这个示例展示了 Skills 的完整工作流程：

1. Level 1 - 元数据加载（启动时）:
   Agent 在启动时自动加载 ~/.claude/skills/news-extractor/SKILL.md 的元数据
   （name 和 description），约 100 tokens

2. Level 2 - 指令加载（触发时）:
   当用户请求匹配 news-extractor 的描述时，Agent 调用 load_skill 工具
   获取详细的操作指令

3. Level 3 - 脚本执行（按需）:
   Agent 按指令执行 scripts/extract_news.py 脚本
   脚本代码不进入上下文，只有输出结果进入上下文

运行方式:
    uv run python examples/extract_article.py

    # 或指定 URL
    uv run python examples/extract_article.py "https://mp.weixin.qq.com/s/xxx"

确保:
    1. 已配置认证（ANTHROPIC_API_KEY）
    2. 已安装 news-extractor skill 到 ~/.claude/skills/news-extractor/
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
from rich.markdown import Markdown

from langchain_skills import LangChainSkillsAgent

console = Console()


def extract_article(url: str):
    """使用 news-extractor Skill 提取文章"""

    console.print(Panel(
        "[bold cyan]文章提取示例[/bold cyan]\n\n"
        "这个示例演示 Skills 的三层加载机制：\n"
        "- Level 1: 元数据已在启动时加载到 system prompt\n"
        "- Level 2: Agent 会调用 load_skill 获取详细指令\n"
        "- Level 3: 执行 extract_news.py 脚本，只有输出进入上下文",
        title="Skills 工作流程演示"
    ))
    console.print()

    # 创建 Agent
    agent = LangChainSkillsAgent()

    # 构造请求
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

    try:
        # 运行 Agent
        result = agent.invoke(prompt)
        response = agent.get_last_response(result)

        console.print("[bold blue]响应:[/bold blue]")
        console.print(Markdown(response))

        console.print()
        console.print(Panel(
            "[green]提取完成![/green]",
            title="执行结果"
        ))

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        console.print("[yellow]提示: 请确保已正确配置 ANTHROPIC_API_KEY[/yellow]")


def main():
    """主函数"""

    # 获取 URL 参数
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # 使用示例 URL（你需要替换成真实的文章 URL）
        url = "https://mp.weixin.qq.com/s/example-article-id"
        console.print(f"[yellow]提示: 未提供 URL，使用示例 URL: {url}[/yellow]")
        console.print("[dim]使用方式: uv run python examples/extract_article.py \"真实的文章URL\"[/dim]")
        console.print()

    extract_article(url)


if __name__ == "__main__":
    main()
