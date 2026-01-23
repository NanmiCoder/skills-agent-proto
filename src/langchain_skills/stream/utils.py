"""
Stream 工具函数和常量

提供统一的辅助函数和常量定义。
"""

from pathlib import Path


# === 状态标记常量 ===
SUCCESS_PREFIX = "[OK]"
FAILURE_PREFIX = "[FAILED]"


# === 显示限制常量 ===
class DisplayLimits:
    """显示相关的长度限制"""
    THINKING_STREAM = 1000      # 流式显示时的 thinking 长度
    THINKING_FINAL = 2000       # 最终显示时的 thinking 长度
    ARGS_INLINE = 100           # 内联显示的参数长度
    ARGS_FORMATTED = 300        # 格式化显示的参数长度
    TOOL_RESULT_STREAM = 500    # 流式显示时的工具结果长度
    TOOL_RESULT_FINAL = 800     # 最终显示时的工具结果长度
    TOOL_RESULT_MAX = 2000      # 工具结果最大长度


def has_args(args) -> bool:
    """
    检查 args 是否有内容

    修复空字典 falsy 问题：空字典 {} 在 Python 中是 falsy，
    但对于工具调用来说，空字典表示无参数，是合法的。

    Args:
        args: 工具参数，可能是 None、{} 或包含参数的字典

    Returns:
        True 如果 args 有实际内容（非 None 且非空字典）
    """
    return args is not None and args != {}


def is_success(content: str) -> bool:
    """
    判断工具输出是否表示成功执行

    基于 [OK]/[FAILED] 前缀判断。

    Args:
        content: 工具输出内容

    Returns:
        True 如果成功执行
    """
    content = content.strip()
    if content.startswith(SUCCESS_PREFIX):
        return True
    if content.startswith(FAILURE_PREFIX):
        return False
    # 其他情况：检测错误模式
    error_patterns = [
        'Traceback (most recent call last)',
        'Exception:',
        'Error:',
    ]
    return not any(pattern in content for pattern in error_patterns)


def resolve_path(file_path: str, working_directory: Path) -> Path:
    """
    解析文件路径，处理相对路径

    Args:
        file_path: 文件路径（绝对或相对）
        working_directory: 工作目录

    Returns:
        解析后的绝对路径
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = working_directory / path
    return path


def truncate(content: str, max_length: int, suffix: str = "\n... (truncated)") -> str:
    """
    截断内容到指定长度

    Args:
        content: 要截断的内容
        max_length: 最大长度
        suffix: 截断后添加的后缀

    Returns:
        截断后的内容
    """
    if len(content) > max_length:
        return content[:max_length] + suffix
    return content
