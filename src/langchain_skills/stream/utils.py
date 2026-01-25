"""
Stream 工具函数和常量

提供统一的辅助函数和常量定义。
"""

import sys
from pathlib import Path, PurePath
from enum import Enum


# === 状态标记常量 ===
SUCCESS_PREFIX = "[OK]"
FAILURE_PREFIX = "[FAILED]"


# === 工具状态指示器 ===
class ToolStatus(str, Enum):
    """工具执行状态指示器（Claude Code 风格）"""
    RUNNING = "●"   # 执行中 - 黄色
    SUCCESS = "●"   # 成功 - 绿色
    ERROR = "●"     # 失败 - 红色
    PENDING = "○"   # 等待 - 灰色


def get_status_symbol(status: ToolStatus) -> str:
    """
    获取状态符号，Windows cmd.exe 使用 ASCII 备选

    在不支持 Unicode 的终端（如 Windows cmd.exe）上，
    圆点符号可能显示为方框，因此提供 ASCII 备选方案。

    Args:
        status: 工具状态

    Returns:
        状态符号（Unicode 或 ASCII）
    """
    # 检测是否支持 Unicode
    try:
        supports_unicode = (
            sys.stdout.encoding
            and 'utf' in sys.stdout.encoding.lower()
        )
    except Exception:
        supports_unicode = False

    if supports_unicode:
        return status.value

    # ASCII 备选
    fallback = {
        ToolStatus.RUNNING: "*",
        ToolStatus.SUCCESS: "+",
        ToolStatus.ERROR: "x",
        ToolStatus.PENDING: "-",
    }
    return fallback.get(status, "?")


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
    解析文件路径，处理相对路径和 ~ 展开

    Args:
        file_path: 文件路径（绝对或相对，支持 ~ 表示用户主目录）
        working_directory: 工作目录

    Returns:
        解析后的绝对路径
    """
    path = Path(file_path).expanduser()  # 处理 ~ 展开
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


# === Claude Code 风格紧凑格式化 ===

def format_tool_compact(name: str, args: dict | None) -> str:
    """
    格式化为 Claude Code 风格的紧凑格式：ToolName(arg1, arg2, ...)

    Args:
        name: 工具名称
        args: 工具参数字典

    Returns:
        格式化的字符串，如 "Bash(git status)" 或 "Read(path/to/file.py)"
    """
    if not args:
        return f"{name}()"

    # 针对常用工具提取关键参数
    name_lower = name.lower()

    if name_lower == "bash":
        cmd = args.get("command", "")
        # 截断过长的命令
        if len(cmd) > 50:
            cmd = cmd[:47] + "..."
        return f"Bash({cmd})"

    elif name_lower == "read":
        path = args.get("file_path", "")
        # 只显示文件名或短路径（跨平台兼容）
        if len(path) > 40:
            path_obj = PurePath(path)
            parts = path_obj.parts
            if len(parts) > 2:
                path = ".../" + "/".join(parts[-2:])  # 统一使用 / 显示
        return f"Read({path})"

    elif name_lower == "write":
        path = args.get("file_path", "")
        if len(path) > 40:
            path_obj = PurePath(path)
            parts = path_obj.parts
            if len(parts) > 2:
                path = ".../" + "/".join(parts[-2:])  # 统一使用 / 显示
        return f"Write({path})"

    elif name_lower == "edit":
        path = args.get("file_path", "")
        if len(path) > 40:
            path_obj = PurePath(path)
            parts = path_obj.parts
            if len(parts) > 2:
                path = ".../" + "/".join(parts[-2:])  # 统一使用 / 显示
        return f"Edit({path})"

    elif name_lower == "glob":
        pattern = args.get("pattern", "")
        if len(pattern) > 40:
            pattern = pattern[:37] + "..."
        return f"Glob({pattern})"

    elif name_lower == "grep":
        pattern = args.get("pattern", "")
        path = args.get("path", ".")
        if len(pattern) > 30:
            pattern = pattern[:27] + "..."
        return f"Grep({pattern}, {path})"

    elif name_lower == "list_dir":
        path = args.get("path", ".")
        return f"ListDir({path})"

    elif name_lower == "load_skill":
        skill_name = args.get("skill_name", "")
        return f"load_skill({skill_name})"

    # 默认格式：显示前几个参数
    params = []
    for k, v in list(args.items())[:2]:
        v_str = str(v)
        if len(v_str) > 20:
            v_str = v_str[:17] + "..."
        params.append(f"{k}={v_str}")

    params_str = ", ".join(params)
    if len(params_str) > 50:
        params_str = params_str[:47] + "..."

    return f"{name}({params_str})"


def format_tree_output(lines: list[str], max_lines: int = 5, indent: str = "  ") -> str:
    """
    将输出格式化为树形结构（Claude Code 风格）

    Args:
        lines: 输出行列表
        max_lines: 最大显示行数
        indent: 缩进字符

    Returns:
        格式化的树形输出字符串

    示例输出:
        └ On branch main
          Your branch is up to date
          ... +16 lines
    """
    if not lines:
        return ""

    result = []
    display_lines = lines[:max_lines]

    for i, line in enumerate(display_lines):
        # 第一行使用 └，后续行使用空格对齐
        prefix = "└" if i == 0 else " "
        result.append(f"{indent}{prefix} {line}")

    # 如果有更多行，显示折叠提示
    remaining = len(lines) - max_lines
    if remaining > 0:
        result.append(f"{indent}  ... +{remaining} lines")

    return "\n".join(result)


def count_lines(content: str) -> int:
    """统计内容行数"""
    if not content:
        return 0
    return len(content.strip().split("\n"))


def truncate_with_line_hint(content: str, max_lines: int = 5) -> tuple[str, int]:
    """
    按行数截断内容，并返回剩余行数

    Args:
        content: 要截断的内容
        max_lines: 最大显示行数

    Returns:
        (截断后的内容, 剩余行数)
    """
    lines = content.strip().split("\n")
    total = len(lines)

    if total <= max_lines:
        return content.strip(), 0

    truncated = "\n".join(lines[:max_lines])
    remaining = total - max_lines
    return truncated, remaining
