#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国新闻提取脚本

使用方式:
    uv run extract_news.py "URL" [--output DIR] [--format json|markdown|both]

支持平台:
    - 微信公众号 (wechat)
    - 今日头条 (toutiao)
    - 网易新闻 (netease)
    - 搜狐新闻 (sohu)
    - 腾讯新闻 (tencent)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# 添加当前目录到路径
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from models import NewsItem
from detector import detect_platform, get_platform_name, PLATFORM_NAMES
from formatter import to_markdown
from crawlers.wechat import WeChatNewsCrawler
from crawlers.toutiao import ToutiaoNewsCrawler
from crawlers.netease import NeteaseNewsCrawler
from crawlers.sohu import SohuNewsCrawler
from crawlers.tencent import TencentNewsCrawler


# 爬虫映射
CRAWLERS = {
    "wechat": WeChatNewsCrawler,
    "toutiao": ToutiaoNewsCrawler,
    "netease": NeteaseNewsCrawler,
    "sohu": SohuNewsCrawler,
    "tencent": TencentNewsCrawler,
}


def log_info(msg: str) -> None:
    """输出信息日志"""
    print(f"[INFO] {msg}")


def log_success(msg: str) -> None:
    """输出成功日志"""
    print(f"[SUCCESS] {msg}")


def log_error(msg: str) -> None:
    """输出错误日志"""
    print(f"[ERROR] {msg}", file=sys.stderr)


def extract_news(
    url: str,
    output_dir: str = "./output",
    output_format: str = "both",
    platform: Optional[str] = None,
) -> int:
    """
    提取新闻内容

    Args:
        url: 新闻 URL
        output_dir: 输出目录
        output_format: 输出格式 (json, markdown, both)
        platform: 指定平台（可选，默认自动检测）

    Returns:
        0 表示成功，1 表示失败
    """
    # 1. 平台检测
    detected_platform = platform or detect_platform(url)

    if not detected_platform:
        log_error("无法识别该平台，请检查 URL 是否正确")
        log_info("支持的中国新闻平台:")
        for pid, pname in PLATFORM_NAMES.items():
            log_info(f"  - {pname} ({pid})")
        return 1

    # 检查是否为支持的平台
    if detected_platform not in CRAWLERS:
        log_error(f"平台 '{detected_platform}' 不支持")
        log_info("支持的中国新闻平台:")
        for pid, pname in PLATFORM_NAMES.items():
            log_info(f"  - {pname} ({pid})")
        return 1

    platform_name = get_platform_name(detected_platform)
    log_info(f"Platform detected: {detected_platform} ({platform_name})")

    # 2. 提取内容
    log_info("Extracting content...")
    try:
        crawler_class = CRAWLERS[detected_platform]
        crawler = crawler_class(url, save_path=output_dir)
        news_item = crawler.run(persist=False)  # 不使用爬虫自带的保存
    except ValueError as e:
        log_error(f"提取失败: {e}")
        return 1
    except Exception as e:
        log_error(f"未知错误: {e}")
        return 1

    # 3. 显示提取结果摘要
    log_info(f"Title: {news_item.title}")
    if news_item.meta_info.author_name:
        log_info(f"Author: {news_item.meta_info.author_name}")
    if news_item.meta_info.publish_time:
        log_info(f"Publish time: {news_item.meta_info.publish_time}")
    log_info(f"Text paragraphs: {len(news_item.texts)}")
    log_info(f"Images: {len(news_item.images)}")
    if news_item.videos:
        log_info(f"Videos: {len(news_item.videos)}")

    # 4. 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 5. 生成输出文件
    news_id = news_item.news_id or "untitled"
    # 清理文件名中的非法字符
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in news_id)

    # JSON 输出
    if output_format in ("json", "both"):
        json_file = output_path / f"{safe_id}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(news_item.to_dict(), f, ensure_ascii=False, indent=2)
        log_success(f"Saved: {json_file}")

    # Markdown 输出
    if output_format in ("markdown", "both"):
        md_file = output_path / f"{safe_id}.md"
        markdown_content = to_markdown(news_item, platform=detected_platform)
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        log_success(f"Saved: {md_file}")

    return 0


def list_platforms() -> None:
    """列出支持的平台"""
    print("支持的中国新闻平台:")
    print()
    for pid, pname in PLATFORM_NAMES.items():
        print(f"  {pname} ({pid})")
    print()
    print("URL 格式示例:")
    print("  - 微信公众号: https://mp.weixin.qq.com/s/xxxxx")
    print("  - 今日头条:   https://www.toutiao.com/article/123456/")
    print("  - 网易新闻:   https://www.163.com/news/article/ABC123.html")
    print("  - 搜狐新闻:   https://www.sohu.com/a/123456_789")
    print("  - 腾讯新闻:   https://news.qq.com/rain/a/20251016A07W8J00")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="中国新闻内容提取工具",
        epilog="支持平台: 微信公众号、今日头条、网易新闻、搜狐新闻、腾讯新闻",
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="新闻 URL",
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="输出目录 (默认: ./output)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "markdown", "both"],
        default="both",
        help="输出格式 (默认: both)",
    )
    parser.add_argument(
        "--platform", "-p",
        choices=list(PLATFORM_NAMES.keys()),
        help="指定平台 (可选，默认自动检测)",
    )
    parser.add_argument(
        "--list-platforms",
        action="store_true",
        help="列出支持的平台",
    )

    args = parser.parse_args()

    # 列出平台
    if args.list_platforms:
        list_platforms()
        return 0

    # 检查 URL 是否提供
    if not args.url:
        parser.print_help()
        return 1

    # 执行提取
    return extract_news(
        url=args.url,
        output_dir=args.output,
        output_format=args.format,
        platform=args.platform,
    )


if __name__ == "__main__":
    sys.exit(main())
