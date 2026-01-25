# LangChain Skills Agent

使用 LangChain 1.0 构建的 Skills Agent，演示 Anthropic Skills 三层加载机制的底层原理。

> **B站视频**: 配合视频《Skills 原理深度解析 + Agent 实战》使用

## 特性

- **Extended Thinking**: 显示模型的思考过程（蓝色面板）
- **流式输出**: Token 级实时显示响应
- **工具调用可视化**: 显示工具名称、参数、执行结果
- **三层 Skills 加载**: Level 1 元数据注入 → Level 2 指令加载 → Level 3 脚本执行

## 快速开始

### 1. 安装

```bash
git clone https://github.com/NanmiCoder/skills-agent-proto.git
cd skills-agent-proto
uv sync
```

### 2. 配置 Claude API Key

创建 `.env` 文件：

> 使用第三方代理中转, 我推荐使用 [接口AI](https://jiekou.ai/referral?invited_code=3CF8T0)，注册绑定github得3刀试用券

```bash
ANTHROPIC_AUTH_TOKEN=sk-xxx
ANTHROPIC_BASE_URL=https://api.jiekou.ai/anthropic
```

### 3. 交互式验证

```bash
uv run langchain-skills --interactive
```

## 三层加载演示

启动后可以观察到完整的三层加载过程：

### Level 1: 启动时 - 元数据注入

```
✓ Discovered 6 skills
  - tornado-erp-module-dev
  - web-design-guidelines
  - news-extractor
  ...
```

Skills 的 name + description 已注入 system prompt，模型知道有哪些能力可用。

### Level 2: 请求匹配时 - 指令加载

```
You: 总结这篇文章 https://mp.weixin.qq.com/s/ohsU1xRrYu9xcVD7qu5lNw

● load_skill(news-extractor)
  └ # Skill: news-extractor
    ## Instructions
    从主流新闻平台提取文章内容...
```

用户请求匹配到 skill 描述，模型主动调用 `load_skill` 获取完整指令。

### Level 3: 执行时 - 脚本运行

```
● Bash(uv run .../extract_news.py https://mp.weixin.qq.com/s/ohsU1xRrYu9xcVD7qu5lNw)
  └ [OK]
    [SUCCESS] Saved: output/xxx.md
```

模型根据指令执行脚本，**脚本代码不进入上下文，只有输出进入**。

## CLI 命令

```bash
# 交互式模式（推荐）
uv run langchain-skills --interactive

# 单次执行
uv run langchain-skills "列出当前目录"

# 禁用 Thinking（降低延迟）
uv run langchain-skills --no-thinking "执行 pwd"

# 查看发现的 Skills
uv run langchain-skills --list-skills

# 查看 System Prompt（Level 1 注入内容）
uv run langchain-skills --show-prompt
```

## 项目结构

```
skills-agent-proto/
├── src/langchain_skills/
│   ├── agent.py          # LangChain Agent (Extended Thinking)
│   ├── cli.py            # CLI 入口 (流式输出)
│   ├── tools.py          # 工具定义 (load_skill, bash, read_file, write_file, glob, grep, edit, list_dir)
│   ├── skill_loader.py   # Skills 发现和加载
│   └── stream/           # 流式处理模块
│       ├── emitter.py    # 事件发射器
│       ├── tracker.py    # 工具调用追踪（支持增量 JSON）
│       ├── formatter.py  # 结果格式化器
│       └── utils.py      # 常量和工具函数
├── tests/                # 单元测试
│   ├── test_stream.py
│   ├── test_cli.py
│   └── test_tools.py
├── docs/                 # 文档
│   ├── skill_introduce.md
│   └── langchain_agent_skill.md
└── .claude/skills/       # 示例 Skills
    └── news-extractor/
        ├── SKILL.md
        └── scripts/extract_news.py
```

## Skills 三层加载机制

| 层级 | 时机 | Token 消耗 | 内容 |
|------|------|------------|------|
| **Level 1** | 启动时 | ~100/Skill | YAML frontmatter (name, description) |
| **Level 2** | 触发时 | <5000 | SKILL.md 完整指令 |
| **Level 3** | 执行时 | 仅输出 | 脚本执行结果（代码不进上下文） |

## 运行测试

```bash
uv run python -m pytest tests/ -v
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` | API Key | 必填 |
| `ANTHROPIC_BASE_URL` | 代理地址 | 官方 API |
| `CLAUDE_MODEL` | 模型名称 | claude-sonnet-4-5-20250929 |
| `MAX_TOKENS` | 最大 tokens | 16000 |

## 参考文档

- [docs/skill_introduce.md](./docs/skill_introduce.md) - Skills 详细介绍
- [docs/langchain_agent_skill.md](./docs/langchain_agent_skill.md) - LangChain 实现说明

## License

MIT
