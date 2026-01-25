# 中国新闻平台 URL 模式说明

本文档描述各平台的 URL 格式和特殊注意事项。

## 平台 URL 模式

### 微信公众号 (wechat)

**URL 格式**:
```
https://mp.weixin.qq.com/s/{article_id}
https://mp.weixin.qq.com/s?__biz=xxx&mid=xxx&idx=xxx&sn=xxx
```

**正则模式**:
```regex
https?://mp\.weixin\.qq\.com/s/
```

**特点**:
- 支持传统页面和 SSR 渲染页面（小红书风格）
- 使用 `curl_cffi` 进行 Chrome 模拟
- 可能需要 Cookie（当前默认配置通常可用）

**示例**:
- `https://mp.weixin.qq.com/s/ebMzDPu2zMT_mRgYgtL6eQ`
- `https://mp.weixin.qq.com/s/RUHJpS9w3RhuhEm94z-1Kw` (SSR 渲染)

---

### 今日头条 (toutiao)

**URL 格式**:
```
https://www.toutiao.com/article/{article_id}/
https://www.toutiao.com/article/{article_id}/?log_from=xxx
```

**正则模式**:
```regex
https?://www\.toutiao\.com/article/
```

**特点**:
- 文章 ID 通常为长数字字符串
- URL 末尾可能有或没有斜杠
- 可能包含 `log_from` 追踪参数

**示例**:
- `https://www.toutiao.com/article/7434425099895210546/`
- `https://www.toutiao.com/article/7404384826024935990/?log_from=xxx`

---

### 网易新闻 (netease)

**URL 格式**:
```
https://www.163.com/news/article/{article_id}.html
https://www.163.com/dy/article/{article_id}.html
```

**正则模式**:
```regex
https?://www\.163\.com/(news|dy)/article/
```

**特点**:
- 支持 `news` 和 `dy`（订阅号）两种路径
- 文章 ID 通常为大写字母数字组合
- 内容在 `div.post_body` 中

**示例**:
- `https://www.163.com/news/article/KC12OUHK000189FH.html`
- `https://www.163.com/dy/article/JK7AUN4S0514R9OJ.html`

---

### 搜狐新闻 (sohu)

**URL 格式**:
```
https://www.sohu.com/a/{article_id}_{source_id}
```

**正则模式**:
```regex
https?://www\.sohu\.com/a/
```

**特点**:
- URL 包含文章 ID 和来源 ID（下划线分隔）
- 图片 URL 可能被加密，需要从 JavaScript 提取真实 URL
- 内容在 `article#mp-editor` 中

**示例**:
- `https://www.sohu.com/a/945014338_160447`

---

### 腾讯新闻 (tencent)

**URL 格式**:
```
https://news.qq.com/rain/a/{article_id}
```

**正则模式**:
```regex
https?://news\.qq\.com/rain/a/
```

**特点**:
- 文章 ID 包含日期和字母数字组合
- 元信息存储在 `window.DATA` JavaScript 变量中
- 内容在 `div.rich_media_content` 中

**示例**:
- `https://news.qq.com/rain/a/20251016A07W8J00`

---

## 平台检测逻辑

检测器使用正则表达式按顺序匹配：

```python
PLATFORM_PATTERNS = {
    "toutiao": r"https?://www\.toutiao\.com/article/",
    "wechat": r"https?://mp\.weixin\.qq\.com/s/",
    "netease": r"https?://www\.163\.com/(news|dy)/article/",
    "sohu": r"https?://www\.sohu\.com/a/",
    "tencent": r"https?://news\.qq\.com/rain/a/",
}
```

## 常见问题

### Q: 为什么提取失败？

可能原因：
1. **Cookie 过期** - 尝试更新 Cookie 配置
2. **页面结构变化** - 平台可能更新了页面模板
3. **反爬策略** - 请求频率过高触发限制
4. **网络问题** - 检查网络连接

### Q: 如何获取新 Cookie？

1. 打开浏览器访问目标平台
2. 打开开发者工具 (F12)
3. 访问一篇文章
4. 在 Network 面板找到主请求
5. 复制 Cookie 头

### Q: 图片无法显示？

某些平台（如微信）的图片有防盗链：
- 微信图片需要特定 Referer
- 搜狐图片可能是加密的 Base64
- 建议在需要时使用 `embed_images=True` 将图片嵌入 Markdown

### Q: 支持批量提取吗？

当前版本仅支持单个 URL 提取。如需批量提取，可以：
1. 使用 shell 循环
2. 或直接调用 `news_extractor_core.services.extractor.ExtractorService`
