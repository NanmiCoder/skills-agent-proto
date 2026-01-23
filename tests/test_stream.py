"""
Stream 模块单元测试

测试 emitter、tracker、formatter、utils 的核心逻辑。
"""

import pytest
from langchain_skills.stream import (
    StreamEventEmitter,
    StreamEvent,
    ToolCallTracker,
    ToolCallInfo,
    ToolResultFormatter,
    ContentType,
    has_args,
    is_success,
    resolve_path,
    truncate,
    DisplayLimits,
    SUCCESS_PREFIX,
    FAILURE_PREFIX,
)
from pathlib import Path


class TestStreamEventEmitter:
    """测试事件发射器"""

    def test_thinking_event(self):
        event = StreamEventEmitter.thinking("test content")
        assert event.type == "thinking"
        assert event.data["content"] == "test content"

    def test_text_event(self):
        event = StreamEventEmitter.text("hello")
        assert event.type == "text"
        assert event.data["content"] == "hello"

    def test_tool_call_event(self):
        event = StreamEventEmitter.tool_call("bash", {"command": "ls"}, "id123")
        assert event.type == "tool_call"
        assert event.data["name"] == "bash"
        assert event.data["args"] == {"command": "ls"}
        assert event.data["id"] == "id123"

    def test_tool_result_event(self):
        event = StreamEventEmitter.tool_result("bash", "[OK]\n\noutput", True)
        assert event.type == "tool_result"
        assert event.data["name"] == "bash"
        assert event.data["success"] is True

    def test_done_event(self):
        event = StreamEventEmitter.done("final response")
        assert event.type == "done"
        assert event.data["response"] == "final response"

    def test_error_event(self):
        event = StreamEventEmitter.error("something went wrong")
        assert event.type == "error"
        assert event.data["message"] == "something went wrong"


class TestToolCallTracker:
    """测试工具调用追踪器"""

    def test_update_and_get(self):
        tracker = ToolCallTracker()
        tracker.update("id1", name="bash", args={"command": "ls"})

        info = tracker.get("id1")
        assert info is not None
        assert info.name == "bash"
        assert info.args == {"command": "ls"}

    def test_incremental_update(self):
        """测试分多次更新的情况"""
        tracker = ToolCallTracker()

        # 第一次只有 name
        tracker.update("id1", name="bash")
        info = tracker.get("id1")
        assert info.name == "bash"
        assert info.args == {}

        # 第二次补充 args
        tracker.update("id1", args={"command": "ls"})
        info = tracker.get("id1")
        assert info.name == "bash"
        assert info.args == {"command": "ls"}

    def test_is_ready_with_name_only(self):
        """测试：只有 name 时应该 ready（修复的 bug）"""
        tracker = ToolCallTracker()
        tracker.update("id1", name="list_files")
        # 无参数工具也应该 ready
        assert tracker.is_ready("id1") is True

    def test_is_ready_with_args(self):
        """测试：有 name 和 args 时应该 ready"""
        tracker = ToolCallTracker()
        tracker.update("id1", name="bash", args={"command": "ls"})
        assert tracker.is_ready("id1") is True

    def test_is_ready_without_name(self):
        """测试：没有 name 时不 ready"""
        tracker = ToolCallTracker()
        tracker.update("id1", args={"command": "ls"})
        assert tracker.is_ready("id1") is False

    def test_mark_emitted(self):
        """测试：标记已发送后不再 ready"""
        tracker = ToolCallTracker()
        tracker.update("id1", name="bash", args={"command": "ls"})
        assert tracker.is_ready("id1") is True

        tracker.mark_emitted("id1")
        assert tracker.is_ready("id1") is False

    def test_get_pending(self):
        """测试获取待处理的工具调用"""
        tracker = ToolCallTracker()
        tracker.update("id1", name="bash", args={"command": "ls"})
        tracker.update("id2", name="read_file", args={"path": "test.txt"})
        tracker.mark_emitted("id1")

        pending = tracker.get_pending()
        assert len(pending) == 1
        assert pending[0].id == "id2"

    def test_emit_all_pending(self):
        """测试发送所有待处理的工具调用"""
        tracker = ToolCallTracker()
        tracker.update("id1", name="bash", args={"command": "ls"})
        tracker.update("id2", name="read_file", args={"path": "test.txt"})

        pending = tracker.emit_all_pending()
        assert len(pending) == 2

        # 发送后应该都被标记
        assert tracker.get("id1").emitted is True
        assert tracker.get("id2").emitted is True

    def test_clear(self):
        """测试清空追踪器"""
        tracker = ToolCallTracker()
        tracker.update("id1", name="bash")
        tracker.clear()
        assert tracker.get("id1") is None

    def test_append_json_delta(self):
        """测试累积 JSON 片段"""
        tracker = ToolCallTracker()
        tracker.update("id1", name="bash")

        # 模拟 LangChain 流式传输中的 input_json_delta
        tracker.append_json_delta('{"command')
        tracker.append_json_delta('": "ls"}')

        tracker.finalize_all()

        info = tracker.get("id1")
        assert info.args == {"command": "ls"}

    def test_append_json_delta_complex(self):
        """测试复杂 JSON 片段累积"""
        tracker = ToolCallTracker()
        tracker.update("id1", name="bash")

        # 更复杂的参数
        tracker.append_json_delta('{"command": "echo ')
        tracker.append_json_delta('hello world", ')
        tracker.append_json_delta('"timeout": 30}')

        tracker.finalize_all()

        info = tracker.get("id1")
        assert info.args == {"command": "echo hello world", "timeout": 30}

    def test_finalize_all_invalid_json(self):
        """测试无效 JSON 不会覆盖原有 args"""
        tracker = ToolCallTracker()
        tracker.update("id1", name="bash", args={"original": "value"})

        tracker.append_json_delta('invalid json {')
        tracker.finalize_all()

        info = tracker.get("id1")
        # 原有 args 应该保持
        assert info.args == {"original": "value"}


class TestToolResultFormatter:
    """测试工具结果格式化器"""

    def test_detect_success(self):
        formatter = ToolResultFormatter()
        assert formatter.detect_type("[OK]\n\nhello") == ContentType.SUCCESS

    def test_detect_error(self):
        formatter = ToolResultFormatter()
        assert formatter.detect_type("[FAILED] Exit code: 1") == ContentType.ERROR

    def test_detect_json(self):
        formatter = ToolResultFormatter()
        assert formatter.detect_type('{"name": "test"}') == ContentType.JSON

    def test_detect_json_with_ok_prefix(self):
        formatter = ToolResultFormatter()
        assert formatter.detect_type('[OK]\n\n{"name": "test"}') == ContentType.JSON

    def test_detect_markdown(self):
        formatter = ToolResultFormatter()
        assert formatter.detect_type("# Title\n\nContent") == ContentType.MARKDOWN

    def test_detect_text(self):
        formatter = ToolResultFormatter()
        assert formatter.detect_type("plain text") == ContentType.TEXT

    def test_is_success_ok(self):
        formatter = ToolResultFormatter()
        assert formatter.is_success("[OK]\n\noutput") is True

    def test_is_success_failed(self):
        formatter = ToolResultFormatter()
        assert formatter.is_success("[FAILED] Exit code: 1") is False

    def test_is_success_traceback(self):
        formatter = ToolResultFormatter()
        content = "Traceback (most recent call last):\n  File..."
        assert formatter.is_success(content) is False

    def test_format_returns_elements(self):
        formatter = ToolResultFormatter()
        result = formatter.format("bash", "[OK]\n\nhello", max_length=100)
        assert result.content_type == ContentType.SUCCESS
        assert result.success is True
        assert len(result.elements) > 0


class TestUtils:
    """测试工具函数"""

    def test_has_args_none(self):
        assert has_args(None) is False

    def test_has_args_empty_dict(self):
        assert has_args({}) is False

    def test_has_args_with_content(self):
        assert has_args({"command": "ls"}) is True

    def test_is_success_ok_prefix(self):
        assert is_success("[OK]\n\noutput") is True

    def test_is_success_failed_prefix(self):
        assert is_success("[FAILED] error") is False

    def test_is_success_traceback(self):
        assert is_success("Traceback (most recent call last):") is False

    def test_is_success_plain(self):
        assert is_success("normal output") is True

    def test_resolve_path_absolute(self):
        path = resolve_path("/absolute/path", Path("/working"))
        assert str(path) == "/absolute/path"

    def test_resolve_path_relative(self):
        path = resolve_path("relative/path", Path("/working"))
        assert str(path) == "/working/relative/path"

    def test_truncate_short(self):
        result = truncate("short", 100)
        assert result == "short"

    def test_truncate_long(self):
        result = truncate("a" * 200, 100)
        assert len(result) < 200
        assert "truncated" in result

    def test_display_limits(self):
        assert DisplayLimits.THINKING_STREAM == 1000
        assert DisplayLimits.TOOL_RESULT_MAX == 2000


class TestConstants:
    """测试常量"""

    def test_success_prefix(self):
        assert SUCCESS_PREFIX == "[OK]"

    def test_failure_prefix(self):
        assert FAILURE_PREFIX == "[FAILED]"
