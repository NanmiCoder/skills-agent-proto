"""
CLI 模块单元测试

测试 StreamState 和相关显示函数。
"""

import pytest
from langchain_skills.cli import StreamState, format_tool_result, format_tool_args


class TestStreamState:
    """测试流式处理状态"""

    def test_init(self):
        state = StreamState()
        assert state.thinking_text == ""
        assert state.response_text == ""
        assert state.tool_calls == []
        assert state.tool_results == []
        assert state.is_thinking is False
        assert state.is_responding is False
        assert state.is_processing is False

    def test_handle_thinking_event(self):
        state = StreamState()
        event_type = state.handle_event({
            "type": "thinking",
            "content": "Let me think..."
        })

        assert event_type == "thinking"
        assert state.thinking_text == "Let me think..."
        assert state.is_thinking is True
        assert state.is_responding is False

    def test_handle_text_event(self):
        state = StreamState()
        event_type = state.handle_event({
            "type": "text",
            "content": "Hello!"
        })

        assert event_type == "text"
        assert state.response_text == "Hello!"
        assert state.is_thinking is False
        assert state.is_responding is True

    def test_handle_tool_call_event(self):
        state = StreamState()
        event_type = state.handle_event({
            "type": "tool_call",
            "name": "bash",
            "args": {"command": "ls"}
        })

        assert event_type == "tool_call"
        assert len(state.tool_calls) == 1
        assert state.tool_calls[0]["name"] == "bash"
        assert state.tool_calls[0]["args"] == {"command": "ls"}

    def test_handle_tool_result_event(self):
        state = StreamState()
        event_type = state.handle_event({
            "type": "tool_result",
            "name": "bash",
            "content": "[OK]\n\nfile1.txt"
        })

        assert event_type == "tool_result"
        assert len(state.tool_results) == 1
        assert state.tool_results[0]["name"] == "bash"
        assert "[OK]" in state.tool_results[0]["content"]
        assert state.is_processing is True  # 工具执行后等待处理

    def test_handle_done_event(self):
        state = StreamState()
        # 没有 response_text 时，从 done 事件获取
        event_type = state.handle_event({
            "type": "done",
            "response": "Final response"
        })

        assert event_type == "done"
        assert state.response_text == "Final response"

    def test_handle_done_event_preserves_existing(self):
        state = StreamState()
        state.response_text = "Already have response"

        state.handle_event({
            "type": "done",
            "response": "Should be ignored"
        })

        # 已有 response_text 时不覆盖
        assert state.response_text == "Already have response"

    def test_accumulate_thinking(self):
        """测试 thinking 内容累积"""
        state = StreamState()
        state.handle_event({"type": "thinking", "content": "First "})
        state.handle_event({"type": "thinking", "content": "Second"})

        assert state.thinking_text == "First Second"

    def test_accumulate_text(self):
        """测试文本内容累积"""
        state = StreamState()
        state.handle_event({"type": "text", "content": "Hello "})
        state.handle_event({"type": "text", "content": "World"})

        assert state.response_text == "Hello World"

    def test_get_display_args(self):
        state = StreamState()
        state.thinking_text = "thinking"
        state.response_text = "response"
        state.is_thinking = True

        args = state.get_display_args()

        assert args["thinking_text"] == "thinking"
        assert args["response_text"] == "response"
        assert args["is_thinking"] is True
        assert "tool_calls" in args
        assert "tool_results" in args
        assert "is_processing" in args

    def test_full_workflow(self):
        """测试完整工作流"""
        state = StreamState()

        # 模拟完整的事件流
        events = [
            {"type": "thinking", "content": "I need to run ls..."},
            {"type": "tool_call", "name": "bash", "args": {"command": "ls"}},
            {"type": "tool_result", "name": "bash", "content": "[OK]\n\nfile1.txt\nfile2.txt"},
            {"type": "text", "content": "Here are the files:\n"},
            {"type": "text", "content": "- file1.txt\n- file2.txt"},
            {"type": "done", "response": ""},
        ]

        for event in events:
            state.handle_event(event)

        assert "ls" in state.thinking_text
        assert len(state.tool_calls) == 1
        assert len(state.tool_results) == 1
        assert "file1.txt" in state.response_text


class TestFormatFunctions:
    """测试格式化函数"""

    def test_format_tool_result_success(self):
        elements = format_tool_result("bash", "[OK]\n\nhello", max_length=100)
        assert len(elements) > 0

    def test_format_tool_result_error(self):
        elements = format_tool_result("bash", "[FAILED] Exit code: 1", max_length=100)
        assert len(elements) > 0

    def test_format_tool_result_json(self):
        elements = format_tool_result("api", '{"status": "ok"}', max_length=100)
        assert len(elements) > 0

    def test_format_tool_args(self):
        elements = format_tool_args({"command": "ls -la"}, max_length=100)
        assert len(elements) > 0

    def test_format_tool_args_truncate(self):
        # 很长的参数应该被截断
        long_args = {"command": "x" * 1000}
        elements = format_tool_args(long_args, max_length=50)
        assert len(elements) > 0
