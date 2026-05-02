"""
LangChain Skills Agent 主体

使用 LangChain 1.0 的 create_agent API 实现 Skills Agent，演示三层加载机制：
- Level 1: 启动时将 Skills 元数据注入 system_prompt
- Level 2: load_skill tool 加载详细指令
- Level 3: bash tool 执行脚本

与 claude-agent-sdk 实现的对比：
- claude-agent-sdk: setting_sources=["user", "project"] 自动处理
- LangChain 实现: 显式调用 SkillLoader，过程透明可见

流式输出支持：
- 支持 Extended Thinking 显示模型思考过程
- 事件级流式输出 (thinking / text / tool_call / tool_result)
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterator

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, AIMessageChunk
from langgraph.checkpoint.memory import InMemorySaver

from .skill_loader import SkillLoader
from .tools import ALL_TOOLS, SkillAgentContext
from .stream import StreamEventEmitter, ToolCallTracker, is_success, DisplayLimits


# 加载环境变量（override=True 确保 .env 文件覆盖系统环境变量）
load_dotenv(override=True)


# 默认配置
DEFAULT_PROVIDER = "anthropic"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_MAX_TOKENS = 16000
DEFAULT_TEMPERATURE = 1.0  # Extended Thinking 要求温度为 1.0
DEFAULT_THINKING_BUDGET = 10000
DEFAULT_OPENAI_REASONING_EFFORT = "medium"


@dataclass(frozen=True)
class ModelConfig:
    """模型初始化配置"""

    provider: str
    model: str
    api_key: str | None
    base_url: str | None
    supports_extended_thinking: bool


def _normalize_provider(provider: str | None) -> str | None:
    """标准化 provider 名称"""
    if provider is None:
        return None

    normalized = provider.strip().lower()
    aliases = {
        "anthropic": "anthropic",
        "claude": "anthropic",
        "openai": "openai",
        "gpt": "openai",
    }
    return aliases.get(normalized, normalized)


def _parse_bool_env(name: str, default: bool) -> bool:
    """解析布尔环境变量"""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_openai_base_url(base_url: str | None) -> str | None:
    """规范化 OpenAI SDK base_url，避免传入完整 endpoint 后被重复拼接。"""
    if not base_url:
        return base_url

    normalized = base_url.rstrip("/")
    for endpoint_suffix in ("/chat/completions", "/responses"):
        if normalized.endswith(endpoint_suffix):
            normalized = normalized[: -len(endpoint_suffix)]
            break

    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


def _split_provider_prefixed_model(model: str | None) -> tuple[str | None, str | None]:
    """解析 provider:model 形式的模型字符串"""
    if not model or ":" not in model:
        return None, model

    raw_provider, raw_model = model.split(":", 1)
    provider = _normalize_provider(raw_provider)
    if provider in ("anthropic", "openai") and raw_model:
        return provider, raw_model
    return None, model


def _infer_provider_from_model_name(model: str | None) -> str | None:
    """根据模型名推断 provider"""
    if not model:
        return None

    model_name = model.strip().lower()
    anthropic_prefixes = ("claude-",)
    openai_prefixes = ("gpt-", "o1", "o3", "o4", "chatgpt-")

    if model_name.startswith(anthropic_prefixes):
        return "anthropic"
    if model_name.startswith(openai_prefixes):
        return "openai"
    return None


def _resolve_requested_provider(model: str | None = None, model_provider: str | None = None) -> str:
    """解析当前请求应使用的 provider"""
    explicit_provider = _normalize_provider(model_provider or os.getenv("MODEL_PROVIDER"))
    prefixed_provider, stripped_model = _split_provider_prefixed_model(model)
    generic_env_provider, generic_env_model = _split_provider_prefixed_model(os.getenv("MODEL_NAME"))

    env_provider_hint = (
        generic_env_provider
        or _infer_provider_from_model_name(generic_env_model)
        or ("openai" if os.getenv("OPENAI_MODEL") else None)
        or ("anthropic" if os.getenv("ANTHROPIC_MODEL") or os.getenv("CLAUDE_MODEL") else None)
    )

    provider = (
        explicit_provider
        or prefixed_provider
        or _infer_provider_from_model_name(stripped_model)
        or env_provider_hint
        or DEFAULT_PROVIDER
    )

    if provider not in ("anthropic", "openai"):
        raise ValueError(f"Unsupported model provider: {provider}")

    return provider


def _resolve_model_name(provider: str, requested_model: str | None = None) -> str:
    """解析模型名称，兼容旧环境变量"""
    requested_provider, stripped_model = _split_provider_prefixed_model(requested_model)
    if requested_provider and requested_provider != provider:
        raise ValueError(
            f"Model provider mismatch: requested '{requested_provider}' but configured '{provider}'"
        )
    if stripped_model:
        return stripped_model

    generic_model = os.getenv("MODEL_NAME")
    generic_provider, stripped_generic_model = _split_provider_prefixed_model(generic_model)
    if generic_provider and generic_provider != provider:
        stripped_generic_model = None
    if stripped_generic_model:
        return stripped_generic_model

    if provider == "openai":
        return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    return (
        os.getenv("ANTHROPIC_MODEL")
        or os.getenv("CLAUDE_MODEL")
        or DEFAULT_ANTHROPIC_MODEL
    )


def _get_provider_credentials(provider: str) -> tuple[str | None, str | None]:
    """
    获取 provider 对应的 API 认证信息

    支持多种认证方式：
    1. 通用配置：MODEL_API_KEY / MODEL_BASE_URL
    2. Provider 专属配置
    3. OpenAI 兼容代理场景下，允许复用 ANTHROPIC_AUTH_TOKEN
       作为 OpenAI 端点的共享平台 Token

    Returns:
        (api_key, base_url) 元组
    """
    api_key = os.getenv("MODEL_API_KEY")
    base_url = os.getenv("MODEL_BASE_URL")

    if provider == "openai":
        api_key = (
            api_key
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("OPENAI_AUTH_TOKEN")
            or os.getenv("ANTHROPIC_AUTH_TOKEN")
            or os.getenv("ANTHROPIC_API_KEY")
        )
        base_url = base_url or os.getenv("OPENAI_BASE_URL")
    else:
        api_key = (
            api_key
            or os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("ANTHROPIC_AUTH_TOKEN")
        )
        base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")

    return api_key, base_url


def resolve_model_config(model: str | None = None, model_provider: str | None = None) -> ModelConfig:
    """解析当前模型配置"""
    provider = _resolve_requested_provider(model=model, model_provider=model_provider)
    model_name = _resolve_model_name(provider, model)
    api_key, base_url = _get_provider_credentials(provider)

    return ModelConfig(
        provider=provider,
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        supports_extended_thinking=(provider in {"anthropic", "openai"}),
    )


def check_api_credentials(model: str | None = None, model_provider: str | None = None) -> bool:
    """检查是否配置了当前 provider 的 API 认证"""
    api_key, _ = _get_provider_credentials(
        _resolve_requested_provider(model=model, model_provider=model_provider)
    )
    return api_key is not None


class LangChainSkillsAgent:
    """
    基于 LangChain 1.0 的 Skills Agent

    演示目的：展示 Skills 三层加载机制的底层原理

    使用示例：
        agent = LangChainSkillsAgent()

        # 查看 system prompt（展示 Level 1）
        print(agent.get_system_prompt())

        # 运行 agent
        for chunk in agent.stream("提取这篇公众号文章"):
            response = agent.get_last_response(chunk)
            if response:
                print(response)
    """

    def __init__(
        self,
        model: Optional[str] = None,
        model_provider: Optional[str] = None,
        skill_paths: Optional[list[Path]] = None,
        working_directory: Optional[Path] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        enable_thinking: bool = True,
        thinking_budget: int = DEFAULT_THINKING_BUDGET,
    ):
        """
        初始化 Agent

        Args:
            model: 模型名称，默认 claude-sonnet-4-5-20250929
            model_provider: 模型提供商，支持 anthropic / openai
            skill_paths: Skills 搜索路径
            working_directory: 工作目录
            max_tokens: 最大 tokens
            temperature: 温度参数 (启用 thinking 时强制为 1.0)
            enable_thinking: 是否启用 Extended Thinking
            thinking_budget: thinking 的 token 预算
        """
        self.model_config = resolve_model_config(model=model, model_provider=model_provider)
        self.model_provider = self.model_config.provider
        self.model_name = self.model_config.model

        # thinking 配置（当前仅 Anthropic 扩展思考链路完整支持）
        self.enable_thinking = enable_thinking and self.model_config.supports_extended_thinking
        self.thinking_budget = thinking_budget

        # 配置 (Anthropic 启用 thinking 时温度必须为 1.0)
        self.max_tokens = max_tokens or int(os.getenv("MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))
        if self.enable_thinking:
            self.temperature = 1.0  # Anthropic 要求启用 thinking 时温度为 1.0
        else:
            self.temperature = (
                temperature
                if temperature is not None
                else float(os.getenv("MODEL_TEMPERATURE", str(DEFAULT_TEMPERATURE)))
            )
        self.working_directory = working_directory or Path.cwd()

        # 初始化 SkillLoader
        self.skill_loader = SkillLoader(skill_paths)

        # Level 1: 构建 system prompt（将 Skills 元数据注入）
        self.system_prompt = self._build_system_prompt()

        # 创建上下文（供 tools 使用）
        self.context = SkillAgentContext(
            skill_loader=self.skill_loader,
            working_directory=self.working_directory,
        )

        # 创建 LangChain Agent
        self.agent = self._create_agent()

    def _build_system_prompt(self) -> str:
        """
        构建 system prompt

        这是 Level 1 的核心：将所有 Skills 的元数据注入到 system prompt。
        每个 skill 约 100 tokens，启动时一次性加载。
        """
        base_prompt = """You are a helpful coding assistant with access to specialized skills.

Your capabilities include:
- Loading and using specialized skills for specific tasks
- Executing bash commands and scripts
- Reading and writing files
- Following skill instructions to complete complex tasks

When a user request matches a skill's description, use the load_skill tool to get detailed instructions before proceeding."""

        return self.skill_loader.build_system_prompt(base_prompt)

    def _create_agent(self):
        """
        创建 LangChain Agent

        使用 LangChain 1.0 的 create_agent API:
        - model: 可以是字符串 ID 或 model 实例
        - tools: 工具列表
        - system_prompt: 系统提示（Level 1 注入 Skills 元数据）
        - context_schema: 上下文类型（供 ToolRuntime 使用）
        - checkpointer: 会话记忆

        Extended Thinking 支持:
        - Anthropic: 使用 thinking budget 获取思考过程
        - OpenAI-compatible: 默认走 chat/completions + reasoning_effort，
          避免部分代理不支持 Responses API

        认证支持:
        - 默认支持 Anthropic
        - 支持 OpenAI / OpenAI-compatible base_url
        - 支持 MODEL_* 通用变量和 provider 专属变量
        """
        # 构建初始化参数
        init_kwargs = {
            "model_provider": self.model_provider,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        base_url = self.model_config.base_url

        # 添加认证参数（支持第三方代理）
        if self.model_config.api_key:
            init_kwargs["api_key"] = self.model_config.api_key

        # Provider-specific thinking / reasoning 配置
        if self.model_provider == "anthropic" and self.enable_thinking:
            init_kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget,
            }
        elif self.model_provider == "openai" and self.enable_thinking:
            use_responses_api = _parse_bool_env("OPENAI_USE_RESPONSES_API", True)
            reasoning_effort = (
                os.getenv("OPENAI_REASONING_EFFORT")
                or os.getenv("MODEL_REASONING_EFFORT")
                or DEFAULT_OPENAI_REASONING_EFFORT
            )
            init_kwargs["use_responses_api"] = use_responses_api
            if use_responses_api:
                init_kwargs["reasoning"] = {
                    "effort": reasoning_effort,
                    "summary": os.getenv("OPENAI_REASONING_SUMMARY", "auto"),
                }
                base_url = _normalize_openai_base_url(base_url)
            else:
                init_kwargs["reasoning_effort"] = reasoning_effort
                base_url = _normalize_openai_base_url(base_url)

        if base_url:
            init_kwargs["base_url"] = base_url

        # 初始化模型
        model = init_chat_model(
            self.model_name,
            **init_kwargs,
        )

        # 创建 Agent
        agent = create_agent(
            model=model,
            tools=ALL_TOOLS,
            system_prompt=self.system_prompt,
            context_schema=SkillAgentContext,
            checkpointer=InMemorySaver(),
        )

        return agent

    def get_system_prompt(self) -> str:
        """
        获取当前 system prompt

        用于演示和调试，展示 Level 1 注入的内容。
        """
        return self.system_prompt

    def get_discovered_skills(self) -> list[dict]:
        """
        获取发现的 Skills 列表

        用于演示 Level 1 的 Skills 发现过程。
        """
        skills = self.skill_loader.scan_skills()
        return [
            {
                "name": s.name,
                "description": s.description,
                "path": str(s.skill_path),
            }
            for s in skills
        ]

    def invoke(self, message: str, thread_id: str = "default") -> dict:
        """
        同步调用 Agent

        Args:
            message: 用户消息
            thread_id: 会话 ID（用于多轮对话）

        Returns:
            Agent 响应
        """
        config = {"configurable": {"thread_id": thread_id}}

        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
            context=self.context,
        )

        return result

    def stream(self, message: str, thread_id: str = "default") -> Iterator[dict]:
        """
        流式调用 Agent (state 级别)

        Args:
            message: 用户消息
            thread_id: 会话 ID

        Yields:
            流式响应块 (完整状态更新)
        """
        config = {"configurable": {"thread_id": thread_id}}

        for chunk in self.agent.stream(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
            context=self.context,
            stream_mode="values",
        ):
            yield chunk

    def stream_events(self, message: str, thread_id: str = "default") -> Iterator[dict]:
        """
        事件级流式输出，支持 thinking 和 token 级流式

        Args:
            message: 用户消息
            thread_id: 会话 ID

        Yields:
            事件字典，格式如下:
            - {"type": "thinking", "content": "..."} - 思考内容片段
            - {"type": "text", "content": "..."} - 响应文本片段
            - {"type": "tool_call", "name": "...", "args": {...}} - 工具调用
            - {"type": "tool_result", "name": "...", "content": "...", "success": bool} - 工具结果
            - {"type": "done", "response": "..."} - 完成标记，包含完整响应
        """
        config = {"configurable": {"thread_id": thread_id}}
        emitter = StreamEventEmitter()
        tracker = ToolCallTracker()

        full_response = ""
        reasoning_tokens = 0
        thinking_seen = False
        debug = os.getenv("SKILLS_DEBUG", "").lower() in ("1", "true", "yes")

        # 使用 messages 模式获取 token 级流式
        try:
            for event in self.agent.stream(
                {"messages": [{"role": "user", "content": message}]},
                config=config,
                context=self.context,
                stream_mode="messages",
            ):
                # event 可能是 tuple(message, metadata) 或直接 message
                if isinstance(event, tuple) and len(event) >= 2:
                    chunk = event[0]
                else:
                    chunk = event

                if debug:
                    chunk_type = type(chunk).__name__
                    print(f"[DEBUG] Event: {chunk_type}")

                # 处理 AIMessageChunk / AIMessage
                if isinstance(chunk, (AIMessageChunk, AIMessage)):
                    reasoning_tokens += self._extract_reasoning_tokens(chunk)
                    # 处理 content
                    for ev in self._process_chunk_content(chunk, emitter, tracker):
                        if ev.type == "thinking":
                            thinking_seen = True
                        if ev.type == "text":
                            full_response += ev.data.get("content", "")
                        if debug:
                            print(f"[DEBUG] Yielding: {ev.type}")
                        yield ev.data

                    # 处理 tool_calls (有些情况下在 chunk.tool_calls 中)
                    if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                        for ev in self._process_tool_calls(chunk.tool_calls, emitter, tracker):
                            if debug:
                                print(f"[DEBUG] Yielding from tool_calls: {ev.type}")
                            yield ev.data

                # 处理 ToolMessage (工具执行结果)
                elif hasattr(chunk, "type") and chunk.type == "tool":
                    if debug:
                        tool_name = getattr(chunk, "name", "unknown")
                        print(f"[DEBUG] Processing tool result: {tool_name}")
                    for ev in self._process_tool_result(chunk, emitter, tracker):
                        if debug:
                            print(f"[DEBUG] Yielding: {ev.type}")
                        yield ev.data

            if debug:
                print("[DEBUG] Stream completed normally")

        except Exception as e:
            if debug:
                import traceback
                print(f"[DEBUG] Stream error: {e}")
                traceback.print_exc()
            # 发送错误事件让用户知道发生了什么
            yield emitter.error(str(e)).data
            raise

        if self.model_provider == "openai" and self.enable_thinking and reasoning_tokens > 0 and not thinking_seen:
            yield emitter.thinking(
                f"[OpenAI reasoning enabled: used {reasoning_tokens} reasoning tokens. "
                "This endpoint does not expose reasoning summary text in the stream.]"
            ).data

        # 发送完成事件
        yield emitter.done(full_response).data

    def _process_chunk_content(self, chunk, emitter: StreamEventEmitter, tracker: ToolCallTracker):
        """处理 chunk 的 content"""
        content = chunk.content

        if isinstance(content, str):
            if content:
                yield emitter.text(content)
                return

        blocks = None
        if hasattr(chunk, "content_blocks"):
            try:
                blocks = chunk.content_blocks
            except Exception:
                blocks = None

        if blocks is None:
            if isinstance(content, dict):
                blocks = [content]
            elif isinstance(content, list):
                blocks = content
            else:
                return

        for raw_block in blocks:
            block = raw_block
            if not isinstance(block, dict):
                if hasattr(block, "model_dump"):
                    block = block.model_dump()
                elif hasattr(block, "dict"):
                    block = block.dict()
                else:
                    continue

            block_type = block.get("type")

            if block_type in ("thinking", "reasoning"):
                thinking_text = block.get("thinking") or block.get("reasoning") or ""
                if thinking_text:
                    yield emitter.thinking(thinking_text)

            elif block_type == "text":
                text = block.get("text") or block.get("content") or ""
                if text:
                    yield emitter.text(text)

            elif block_type in ("tool_use", "tool_call"):
                tool_id = block.get("id", "")
                name = block.get("name", "")
                args = block.get("input") if block_type == "tool_use" else block.get("args")
                args_payload = args if isinstance(args, dict) else {}

                if tool_id:
                    tracker.update(tool_id, name=name, args=args_payload)
                    # 立即发送（显示"执行中"状态），参数可能尚不完整
                    if tracker.is_ready(tool_id):
                        tracker.mark_emitted(tool_id)
                        yield emitter.tool_call(name, args_payload, tool_id)

            elif block_type == "input_json_delta":
                # 累积 JSON 片段（args 分批到达）
                partial_json = block.get("partial_json", "")
                if partial_json:
                    tracker.append_json_delta(partial_json, block.get("index", 0))

            elif block_type == "tool_call_chunk":
                tool_id = block.get("id", "")
                name = block.get("name", "")
                if tool_id:
                    tracker.update(tool_id, name=name)
                partial_args = block.get("args", "")
                if isinstance(partial_args, str) and partial_args:
                    tracker.append_json_delta(partial_args, block.get("index", 0))

    def _handle_tool_use_block(self, block: dict, emitter: StreamEventEmitter, tracker: ToolCallTracker):
        """处理 tool_use 块 - 立即发送 tool_call 事件

        在收到 tool_use 时立即发送，让 CLI 可以显示"正在执行"状态。
        避免重复发送（同一 tool 可能通过多个路径到达）。
        """
        tool_id = block.get("id", "")
        if tool_id:
            name = block.get("name", "")
            args = block.get("input", {})
            args_payload = args if isinstance(args, dict) else {}

            tracker.update(tool_id, name=name, args=args_payload)
            if tracker.is_ready(tool_id):
                tracker.mark_emitted(tool_id)
                yield emitter.tool_call(name, args_payload, tool_id)

    def _process_tool_calls(self, tool_calls: list, emitter: StreamEventEmitter, tracker: ToolCallTracker):
        """处理 chunk.tool_calls - 立即发送 tool_call 事件

        避免重复发送（同一 tool 可能通过 tool_use block 已发送）。
        """
        for tc in tool_calls:
            tool_id = tc.get("id", "")
            if tool_id:
                name = tc.get("name", "")
                args = tc.get("args", {})
                args_payload = args if isinstance(args, dict) else {}

                tracker.update(tool_id, name=name, args=args_payload)
                if tracker.is_ready(tool_id):
                    tracker.mark_emitted(tool_id)
                    yield emitter.tool_call(name, args_payload, tool_id)

    def _process_tool_result(self, chunk, emitter: StreamEventEmitter, tracker: ToolCallTracker):
        """处理工具结果"""
        # 最终化：解析累积的 JSON 片段为 args
        tracker.finalize_all()

        # 发送所有工具调用的更新（参数现在是完整的）
        # CLI 会用 tool_id 去重和更新
        for info in tracker.get_all():
            yield emitter.tool_call(info.name, info.args, info.id)

        # 发送结果
        name = getattr(chunk, "name", "unknown")
        raw_content = str(getattr(chunk, "content", ""))
        content = raw_content[:DisplayLimits.TOOL_RESULT_MAX]
        if len(raw_content) > DisplayLimits.TOOL_RESULT_MAX:
            content += "\n... (truncated)"

        # 基于内容判断是否成功（统一使用 is_success）
        success = is_success(content)

        yield emitter.tool_result(name, content, success)

    def _extract_reasoning_tokens(self, chunk) -> int:
        """从 OpenAI chunk 的 usage_metadata 中提取 reasoning token 数量"""
        usage_metadata = getattr(chunk, "usage_metadata", None) or {}
        output_details = usage_metadata.get("output_token_details") or {}
        reasoning_tokens = output_details.get("reasoning", 0)
        return reasoning_tokens if isinstance(reasoning_tokens, int) else 0

    def get_last_response(self, result: dict) -> str:
        """
        从结果中提取最后的 AI 响应文本

        Args:
            result: invoke 或 stream 的结果

        Returns:
            AI 响应文本
        """
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                if isinstance(msg.content, str):
                    return msg.content
                elif isinstance(msg.content, list):
                    # 处理多部分内容
                    text_parts = []
                    for part in msg.content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif isinstance(part, str):
                            text_parts.append(part)
                    return "\n".join(text_parts)
        return ""


def create_skills_agent(
    model: Optional[str] = None,
    model_provider: Optional[str] = None,
    skill_paths: Optional[list[Path]] = None,
    working_directory: Optional[Path] = None,
    enable_thinking: bool = True,
    thinking_budget: int = DEFAULT_THINKING_BUDGET,
) -> LangChainSkillsAgent:
    """
    便捷函数：创建 Skills Agent

    Args:
        model: 模型名称
        model_provider: 模型提供商
        skill_paths: Skills 搜索路径
        working_directory: 工作目录
        enable_thinking: 是否启用 Extended Thinking
        thinking_budget: thinking 的 token 预算

    Returns:
        配置好的 LangChainSkillsAgent 实例
    """
    return LangChainSkillsAgent(
        model=model,
        model_provider=model_provider,
        skill_paths=skill_paths,
        working_directory=working_directory,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget,
    )
