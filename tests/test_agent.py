"""Agent provider routing tests."""

from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import Mock, patch

from langchain_skills.agent import LangChainSkillsAgent, resolve_model_config


@contextmanager
def openai_compatible_chat_server():
    requests: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 - stdlib callback name
            body = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
            payload = json.loads(body.decode("utf-8"))
            requests.append({"path": self.path, "payload": payload})

            if payload.get("stream"):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                chunks = [
                    {
                        "id": "chatcmpl-test",
                        "object": "chat.completion.chunk",
                        "created": 0,
                        "model": payload.get("model", "deepseek-r1"),
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant", "content": "PING"},
                                "finish_reason": None,
                            }
                        ],
                    },
                    {
                        "id": "chatcmpl-test",
                        "object": "chat.completion.chunk",
                        "created": 0,
                        "model": payload.get("model", "deepseek-r1"),
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    },
                ]
                for chunk in chunks:
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                self.wfile.write(b"data: [DONE]\n\n")
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "created": 0,
                "model": payload.get("model", "deepseek-r1"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "PING"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))

        def log_message(self, format, *args):  # noqa: A002 - stdlib callback signature
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_resolve_model_config_defaults_to_anthropic_legacy_env():
    with patch.dict(
        os.environ,
        {
            "ANTHROPIC_AUTH_TOKEN": "anthropic-token",
            "ANTHROPIC_BASE_URL": "https://api.jiekou.ai/anthropic",
            "CLAUDE_MODEL": "claude-sonnet-4-5-20250929",
        },
        clear=True,
    ):
        config = resolve_model_config()

    assert config.provider == "anthropic"
    assert config.model == "claude-sonnet-4-5-20250929"
    assert config.api_key == "anthropic-token"
    assert config.base_url == "https://api.jiekou.ai/anthropic"
    assert config.supports_extended_thinking is True


def test_resolve_model_config_supports_openai_generic_env():
    with patch.dict(
        os.environ,
        {
            "MODEL_PROVIDER": "openai",
            "MODEL_NAME": "gpt-5.4",
            "MODEL_API_KEY": "shared-token",
            "MODEL_BASE_URL": "https://api.jiekou.ai/openai",
        },
        clear=True,
    ):
        config = resolve_model_config()

    assert config.provider == "openai"
    assert config.model == "gpt-5.4"
    assert config.api_key == "shared-token"
    assert config.base_url == "https://api.jiekou.ai/openai"
    assert config.supports_extended_thinking is True


def test_resolve_model_config_supports_openai_provider_specific_env():
    with patch.dict(
        os.environ,
        {
            "OPENAI_MODEL": "gpt-5.4",
            "OPENAI_API_KEY": "openai-token",
            "OPENAI_BASE_URL": "https://api.jiekou.ai/openai",
        },
        clear=True,
    ):
        config = resolve_model_config()

    assert config.provider == "openai"
    assert config.model == "gpt-5.4"
    assert config.api_key == "openai-token"
    assert config.base_url == "https://api.jiekou.ai/openai"


def test_openai_agent_enables_reasoning_effort_kwargs():
    fake_loader = Mock()
    fake_loader.build_system_prompt.return_value = "system prompt"

    with patch.dict(
        os.environ,
        {
            "MODEL_PROVIDER": "openai",
            "MODEL_NAME": "gpt-5.4",
            "MODEL_API_KEY": "shared-token",
            "MODEL_BASE_URL": "https://api.jiekou.ai/openai",
        },
        clear=True,
    ), patch("langchain_skills.agent.SkillLoader", return_value=fake_loader), patch(
        "langchain_skills.agent.init_chat_model"
    ) as init_chat_model, patch("langchain_skills.agent.create_agent", return_value=object()):
        init_chat_model.return_value = object()
        agent = LangChainSkillsAgent(enable_thinking=True)

    kwargs = init_chat_model.call_args.kwargs
    assert agent.model_provider == "openai"
    assert agent.enable_thinking is True
    assert kwargs["model_provider"] == "openai"
    assert kwargs["api_key"] == "shared-token"
    assert kwargs["base_url"] == "https://api.jiekou.ai/openai/v1"
    assert kwargs["use_responses_api"] is True
    assert kwargs["reasoning"] == {"effort": "medium", "summary": "auto"}
    assert "thinking" not in kwargs


def test_openai_chat_completions_adds_v1_to_proxy_base_url():
    fake_loader = Mock()
    fake_loader.build_system_prompt.return_value = "system prompt"

    with patch.dict(
        os.environ,
        {
            "MODEL_PROVIDER": "openai",
            "MODEL_NAME": "deepseek-r1",
            "MODEL_API_KEY": "shared-token",
            "MODEL_BASE_URL": "https://api.example.test/openai",
            "OPENAI_USE_RESPONSES_API": "false",
        },
        clear=True,
    ), patch("langchain_skills.agent.SkillLoader", return_value=fake_loader), patch(
        "langchain_skills.agent.init_chat_model"
    ) as init_chat_model, patch("langchain_skills.agent.create_agent", return_value=object()):
        init_chat_model.return_value = object()
        LangChainSkillsAgent(enable_thinking=True)

    kwargs = init_chat_model.call_args.kwargs
    assert kwargs["base_url"] == "https://api.example.test/openai/v1"
    assert kwargs["use_responses_api"] is False
    assert kwargs["reasoning_effort"] == "medium"


def test_openai_chat_completions_accepts_full_endpoint_base_url():
    fake_loader = Mock()
    fake_loader.build_system_prompt.return_value = "system prompt"

    with patch.dict(
        os.environ,
        {
            "MODEL_PROVIDER": "openai",
            "MODEL_NAME": "deepseek-r1",
            "MODEL_API_KEY": "shared-token",
            "MODEL_BASE_URL": "https://api.example.test/openai/v1/chat/completions",
            "OPENAI_USE_RESPONSES_API": "false",
        },
        clear=True,
    ), patch("langchain_skills.agent.SkillLoader", return_value=fake_loader), patch(
        "langchain_skills.agent.init_chat_model"
    ) as init_chat_model, patch("langchain_skills.agent.create_agent", return_value=object()):
        init_chat_model.return_value = object()
        LangChainSkillsAgent(enable_thinking=True)

    kwargs = init_chat_model.call_args.kwargs
    assert kwargs["base_url"] == "https://api.example.test/openai/v1"
    assert kwargs["use_responses_api"] is False


def test_openai_compatible_chat_completions_streams_end_to_end():
    with openai_compatible_chat_server() as (server_url, requests), patch.dict(
        os.environ,
        {
            "MODEL_PROVIDER": "openai",
            "MODEL_NAME": "deepseek-r1",
            "MODEL_API_KEY": "shared-token",
            "MODEL_BASE_URL": f"{server_url}/openai",
            "OPENAI_USE_RESPONSES_API": "false",
        },
        clear=True,
    ):
        agent = LangChainSkillsAgent(skill_paths=[], enable_thinking=True)
        events = list(agent.stream_events("Return exactly PING.", thread_id="openai-compatible-e2e"))

    text = "".join(event.get("content", "") for event in events if event["type"] == "text")

    assert text == "PING"
    assert events[-1] == {"type": "done", "response": "PING"}
    assert requests[0]["path"] == "/openai/v1/chat/completions"
    assert requests[0]["payload"]["model"] == "deepseek-r1"
    assert requests[0]["payload"]["stream"] is True


def test_openai_compatible_full_endpoint_streams_without_duplicate_path():
    with openai_compatible_chat_server() as (server_url, requests), patch.dict(
        os.environ,
        {
            "MODEL_PROVIDER": "openai",
            "MODEL_NAME": "deepseek-r1",
            "MODEL_API_KEY": "shared-token",
            "MODEL_BASE_URL": f"{server_url}/openai/v1/chat/completions",
            "OPENAI_USE_RESPONSES_API": "false",
        },
        clear=True,
    ):
        agent = LangChainSkillsAgent(skill_paths=[], enable_thinking=True)
        events = list(agent.stream_events("Return exactly PING.", thread_id="openai-full-endpoint-e2e"))

    text = "".join(event.get("content", "") for event in events if event["type"] == "text")

    assert text == "PING"
    assert requests[0]["path"] == "/openai/v1/chat/completions"


def test_anthropic_agent_keeps_thinking_kwargs():
    fake_loader = Mock()
    fake_loader.build_system_prompt.return_value = "system prompt"

    with patch.dict(
        os.environ,
        {
            "MODEL_PROVIDER": "anthropic",
            "MODEL_NAME": "claude-sonnet-4-5-20250929",
            "MODEL_API_KEY": "anthropic-token",
            "MODEL_BASE_URL": "https://api.jiekou.ai/anthropic",
        },
        clear=True,
    ), patch("langchain_skills.agent.SkillLoader", return_value=fake_loader), patch(
        "langchain_skills.agent.init_chat_model"
    ) as init_chat_model, patch("langchain_skills.agent.create_agent", return_value=object()):
        init_chat_model.return_value = object()
        agent = LangChainSkillsAgent(enable_thinking=True, thinking_budget=2048)

    kwargs = init_chat_model.call_args.kwargs
    assert agent.model_provider == "anthropic"
    assert agent.enable_thinking is True
    assert kwargs["model_provider"] == "anthropic"
    assert kwargs["thinking"] == {"type": "enabled", "budget_tokens": 2048}
    assert kwargs["api_key"] == "anthropic-token"
    assert kwargs["base_url"] == "https://api.jiekou.ai/anthropic"
