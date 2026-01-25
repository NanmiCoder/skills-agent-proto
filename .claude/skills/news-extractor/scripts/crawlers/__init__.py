# -*- coding: utf-8 -*-
"""
爬虫模块
"""
from .wechat import WeChatNewsCrawler
from .toutiao import ToutiaoNewsCrawler
from .netease import NeteaseNewsCrawler
from .sohu import SohuNewsCrawler
from .tencent import TencentNewsCrawler

__all__ = [
    "WeChatNewsCrawler",
    "ToutiaoNewsCrawler",
    "NeteaseNewsCrawler",
    "SohuNewsCrawler",
    "TencentNewsCrawler",
]
