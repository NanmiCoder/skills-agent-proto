"""
ToolCallTracker - 工具调用追踪器

管理流式传输中的工具调用状态，处理增量到达的参数。
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ToolCallInfo:
    """工具调用信息"""
    id: str
    name: str
    args: Dict = field(default_factory=dict)
    emitted: bool = False
    # 用于累积 input_json_delta 片段
    _json_buffer: str = ""


class ToolCallTracker:
    """工具调用追踪器

    处理 LangChain 流式输出中 tool_use 块的增量到达问题。
    支持 input_json_delta 类型的增量 JSON 片段累积。

    使用示例：
        tracker = ToolCallTracker()

        # 注册工具调用（可能分多次到达）
        tracker.update(tool_id, name="bash")

        # 累积 JSON 片段
        tracker.append_json_delta(tool_id, '{"command')
        tracker.append_json_delta(tool_id, '": "ls"}')

        # 最终化：解析累积的 JSON
        tracker.finalize(tool_id)

        # 发送
        info = tracker.get(tool_id)
        yield emitter.tool_call(info.name, info.args)
    """

    def __init__(self):
        self._calls: Dict[str, ToolCallInfo] = {}
        # 记录最后一个 tool_id（用于 input_json_delta 没有 id 的情况）
        self._last_tool_id: Optional[str] = None

    def update(
        self,
        tool_id: str,
        name: Optional[str] = None,
        args: Optional[Dict] = None,
    ) -> None:
        """更新工具调用信息（累积式）"""
        if tool_id not in self._calls:
            self._calls[tool_id] = ToolCallInfo(id=tool_id, name=name or "", args=args or {})
            self._last_tool_id = tool_id
        else:
            info = self._calls[tool_id]
            if name:
                info.name = name
            if args:
                info.args = args

    def append_json_delta(self, partial_json: str, index: int = 0) -> None:
        """累积 input_json_delta 片段

        LangChain 流式传输中，args 可能以 input_json_delta 形式分批到达。
        index 用于处理并行工具调用的情况。
        """
        # 使用 last_tool_id（因为 input_json_delta 没有 tool_id）
        tool_id = self._last_tool_id
        if tool_id and tool_id in self._calls:
            self._calls[tool_id]._json_buffer += partial_json

    def finalize_all(self) -> None:
        """最终化所有工具调用：解析累积的 JSON 片段"""
        for info in self._calls.values():
            if info._json_buffer:
                try:
                    info.args = json.loads(info._json_buffer)
                except json.JSONDecodeError:
                    pass  # 保持原有 args
                info._json_buffer = ""

    def is_ready(self, tool_id: str) -> bool:
        """检查工具调用是否准备好发送（有 name 即可，args 可为空）"""
        if tool_id not in self._calls:
            return False
        info = self._calls[tool_id]
        # 只要有 name 且未发送即可，args 为空字典是合法的（某些工具无参数）
        return bool(info.name) and not info.emitted

    def mark_emitted(self, tool_id: str) -> None:
        """标记已发送"""
        if tool_id in self._calls:
            self._calls[tool_id].emitted = True

    def get(self, tool_id: str) -> Optional[ToolCallInfo]:
        """获取工具调用信息"""
        return self._calls.get(tool_id)

    def get_pending(self) -> list[ToolCallInfo]:
        """获取所有未发送的工具调用"""
        return [info for info in self._calls.values() if not info.emitted]

    def emit_all_pending(self) -> list[ToolCallInfo]:
        """发送所有待处理的工具调用并标记"""
        pending = self.get_pending()
        for info in pending:
            info.emitted = True
        return pending

    def clear(self) -> None:
        """清空追踪器"""
        self._calls.clear()
