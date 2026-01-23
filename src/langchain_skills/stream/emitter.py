"""
StreamEventEmitter - 统一事件格式

所有事件都包含 type 和相关数据。
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class StreamEvent:
    """统一的流式事件"""
    type: str
    data: Dict[str, Any]


class StreamEventEmitter:
    """流式事件发射器"""

    @staticmethod
    def thinking(content: str, thinking_id: int = 0) -> StreamEvent:
        """思考内容事件"""
        return StreamEvent("thinking", {"type": "thinking", "content": content, "id": thinking_id})

    @staticmethod
    def text(content: str) -> StreamEvent:
        """文本内容事件"""
        return StreamEvent("text", {"type": "text", "content": content})

    @staticmethod
    def tool_call(name: str, args: Dict[str, Any], tool_id: str = "") -> StreamEvent:
        """工具调用事件"""
        return StreamEvent("tool_call", {"type": "tool_call", "name": name, "args": args, "id": tool_id})

    @staticmethod
    def tool_result(name: str, content: str, success: bool = True) -> StreamEvent:
        """工具结果事件"""
        return StreamEvent("tool_result", {
            "type": "tool_result",
            "name": name,
            "content": content,
            "success": success,
        })

    @staticmethod
    def done(response: str = "") -> StreamEvent:
        """完成事件"""
        return StreamEvent("done", {"type": "done", "response": response})

    @staticmethod
    def error(message: str) -> StreamEvent:
        """错误事件"""
        return StreamEvent("error", {"type": "error", "message": message})
