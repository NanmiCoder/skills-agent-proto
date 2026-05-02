# LangChain Skills Agent

使用 LangChain 1.0 构建的 Skills Agent，演示 Skills 三层加载机制的底层原理。默认使用 Anthropic，也支持 OpenAI / OpenAI-compatible 接口。

> **B站视频**: [Skills到底怎么实现？我写了个Agent跑给你看](https://www.bilibili.com/video/BV1ZpzhBLE82)

## 特性

- **多 Provider 支持**: 默认 Anthropic，支持 OpenAI / OpenAI-compatible Base URL
- **Extended Thinking**: Anthropic 模型可显示思考过程（蓝色面板）
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

### 2. 配置模型 API

默认文档仍以 Anthropic 为例；如果你使用接口AI 这类 OpenAI-compatible 代理，也可以切到 OpenAI 协议。

#### Anthropic（默认）

创建 `.env` 文件：

> 使用第三方代理中转, 我推荐使用 [接口AI](https://jiekou.ai/referral?invited_code=3CF8T0)，注册绑定github得3刀试用券

```bash
MODEL_PROVIDER=anthropic
MODEL_NAME=claude-sonnet-4-5-20250929
MODEL_API_KEY=sk-xxx
MODEL_BASE_URL=https://api.jiekou.ai/anthropic
```

兼容旧配置，下面这些变量仍然可用：

```bash
ANTHROPIC_AUTH_TOKEN=sk-xxx
ANTHROPIC_BASE_URL=https://api.jiekou.ai/anthropic
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

#### OpenAI / OpenAI-compatible

如果你要切到 OpenAI 协议，把 provider、model 和 base URL 切过去即可。接口AI 示例：

```bash
MODEL_PROVIDER=openai
MODEL_NAME=gpt-5.4
MODEL_API_KEY=sk-xxx
MODEL_BASE_URL=https://api.jiekou.ai/openai
```

开启 OpenAI thinking 时，项目默认会走 Responses API，并自动把上面的 base URL 规范成 `https://api.jiekou.ai/openai/v1`，这样 `gpt-5.4` 的 reasoning 和 tool calling 可以同时工作。

也支持 OpenAI 专属变量：

```bash
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.jiekou.ai/openai
OPENAI_MODEL=gpt-5.4
OPENAI_REASONING_EFFORT=medium
```

如果你的代理只支持 `chat/completions`，可以显式关闭：

```bash
OPENAI_USE_RESPONSES_API=false
```

这种模式下 `MODEL_BASE_URL` / `OPENAI_BASE_URL` 可以填到兼容服务的 base 层级，例如 `https://api.jiekou.ai/openai` 或 `https://api.jiekou.ai/openai/v1`。如果误填到完整 endpoint，例如 `.../v1/chat/completions`，项目会自动裁剪回 SDK 需要的 `.../v1`，避免重复拼接路径。

### 3. 交互式验证

```bash
uv run langchain-skills --interactive
```

启动后会显示当前实际使用的 `provider:model`，方便确认是否已经切到 OpenAI。

## 三层加载演示

![Skills Agent 交互流程](docs/images/basic.png)

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

# 禁用 Thinking（降低延迟；OpenAI 默认走标准流式输出）
uv run langchain-skills --no-thinking "执行 pwd"

# 查看发现的 Skills
uv run langchain-skills --list-skills

# 查看 System Prompt（Level 1 注入内容）
uv run langchain-skills --show-prompt
```

## Web Demo（React + FastAPI + SSE）

### 一键启动（推荐）

```bash
./start.sh
```

脚本会自动执行：
- `uv sync`（后端依赖安装）
- `web/npm install`（前端依赖安装）
- 启动 FastAPI（8000）和 Vite（5173）

### 1. 启动后端 API（端口 8000）

```bash
uv run langchain-skills-web
```

等价命令：

```bash
uv run uvicorn langchain_skills.web_api:app --reload --port 8000
```

### 2. 启动前端（端口 5173）

```bash
cd web
npm install
npm run dev
```

默认会连接 `http://localhost:8000`，如需修改：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

### 3. Web 交互能力

- 打开页面即显示已发现 Skills（name / description / path）
- 底部输入框支持多轮对话和手动新建 thread
- SSE 实时显示 `thinking`、`tool_call`、`tool_result`、`text`、`done`、`error`
- 当调用 `load_skill` 时，UI 会明确标记当前识别到的 skill
- 支持命令：
  - `/skills` 显示可用技能列表
  - `/prompt` 显示当前 system prompt

## 项目结构

```
skills-agent-proto/
├── src/langchain_skills/
│   ├── agent.py          # LangChain Agent (Anthropic/OpenAI provider routing)
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
| `MODEL_PROVIDER` | 通用 provider，`anthropic` / `openai` | `anthropic` |
| `MODEL_NAME` | 通用模型名 | `claude-opus-4-5-20251101` |
| `MODEL_API_KEY` | 通用 API Key / 平台 Token | 无 |
| `MODEL_BASE_URL` | 通用 Base URL | 官方 API |
| `ANTHROPIC_AUTH_TOKEN` | Anthropic 兼容旧配置 | 无 |
| `ANTHROPIC_BASE_URL` | Anthropic Base URL | 官方 API |
| `CLAUDE_MODEL` | Anthropic 兼容旧模型变量 | `claude-opus-4-5-20251101` |
| `OPENAI_API_KEY` | OpenAI API Key | 无 |
| `OPENAI_BASE_URL` | OpenAI / 兼容接口 Base URL | 官方 API |
| `OPENAI_MODEL` | OpenAI 模型名 | `gpt-5-mini` |
| `OPENAI_REASONING_EFFORT` | OpenAI thinking 强度 | `medium` |
| `OPENAI_USE_RESPONSES_API` | 是否使用 Responses API | `true` |
| `MAX_TOKENS` | 最大输出 tokens | `16000` |
| `MODEL_TEMPERATURE` | 模型温度 | `1.0` |

> 建议优先使用 `MODEL_*` 通用变量；这样在 Anthropic 和 OpenAI 之间切换时只需要改 provider、model、base_url。

## 参考文档

- [docs/skill_introduce.md](./docs/skill_introduce.md) - Skills 详细介绍
- [docs/langchain_agent_skill.md](./docs/langchain_agent_skill.md) - LangChain 实现说明
- [LangChain ChatOpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai) - OpenAI 集成
- [LangChain Models / base_url](https://docs.langchain.com/oss/python/langchain/models) - OpenAI-compatible Base URL 配置

## License

MIT
