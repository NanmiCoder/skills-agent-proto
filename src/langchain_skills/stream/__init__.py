"""
Stream 子模块 - 流式事件处理

提供:
- StreamEventEmitter: 事件发射器
- ToolCallTracker: 工具调用追踪器
- ToolResultFormatter: 工具结果格式化器
- 工具函数: has_args, is_success, resolve_path, truncate, get_status_symbol
- 常量: SUCCESS_PREFIX, FAILURE_PREFIX, DisplayLimits
"""

from .emitter import StreamEventEmitter, StreamEvent
from .tracker import ToolCallTracker, ToolCallInfo
from .formatter import ToolResultFormatter, ContentType, FormattedResult
from .utils import (
    SUCCESS_PREFIX,
    FAILURE_PREFIX,
    ToolStatus,
    DisplayLimits,
    has_args,
    is_success,
    resolve_path,
    truncate,
    format_tool_compact,
    format_tree_output,
    count_lines,
    truncate_with_line_hint,
    get_status_symbol,
)

__all__ = [
    # Emitter
    "StreamEventEmitter",
    "StreamEvent",
    # Tracker
    "ToolCallTracker",
    "ToolCallInfo",
    # Formatter
    "ToolResultFormatter",
    "ContentType",
    "FormattedResult",
    # Utils
    "SUCCESS_PREFIX",
    "FAILURE_PREFIX",
    "ToolStatus",
    "DisplayLimits",
    "has_args",
    "is_success",
    "resolve_path",
    "truncate",
    "format_tool_compact",
    "format_tree_output",
    "count_lines",
    "truncate_with_line_hint",
    "get_status_symbol",
]
