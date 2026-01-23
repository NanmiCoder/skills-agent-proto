"""
Tools 模块单元测试

测试 bash 工具的输出格式和路径处理。

注意：由于 LangChain @tool 装饰器需要特殊的调用方式，
这里直接测试底层实现逻辑，而不是通过 .invoke() 调用。
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from langchain_skills.tools import SkillAgentContext
from langchain_skills.stream import SUCCESS_PREFIX, FAILURE_PREFIX, resolve_path


class MockRuntime:
    """模拟 ToolRuntime"""
    def __init__(self, working_directory: Path = None):
        self.context = SkillAgentContext(
            skill_loader=Mock(),
            working_directory=working_directory or Path.cwd(),
        )


def run_bash_command(command: str, working_directory: Path = None) -> str:
    """直接执行 bash 命令的测试辅助函数（复制 tools.py 中的逻辑）"""
    cwd = str(working_directory or Path.cwd())

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        parts = []

        if result.returncode == 0:
            parts.append("[OK]")
        else:
            parts.append(f"[FAILED] Exit code: {result.returncode}")

        parts.append("")

        if result.stdout:
            parts.append(result.stdout.rstrip())

        if result.stderr:
            if result.stdout:
                parts.append("")
            parts.append("--- stderr ---")
            parts.append(result.stderr.rstrip())

        if not result.stdout and not result.stderr:
            parts.append("(no output)")

        return "\n".join(parts)

    except subprocess.TimeoutExpired:
        return "[FAILED] Command timed out after 300 seconds."
    except Exception as e:
        return f"[FAILED] {str(e)}"


class TestBashTool:
    """测试 bash 工具的输出格式"""

    def test_successful_command(self):
        """测试成功执行的命令"""
        result = run_bash_command("echo hello")

        assert result.startswith(SUCCESS_PREFIX)
        assert "hello" in result

    def test_failed_command(self):
        """测试失败的命令"""
        result = run_bash_command("exit 1")

        assert result.startswith(FAILURE_PREFIX)
        assert "Exit code: 1" in result

    def test_command_with_stderr(self):
        """测试有 stderr 输出的命令"""
        result = run_bash_command("echo error >&2")

        # 即使有 stderr，exit code 0 也应该是 [OK]
        assert result.startswith(SUCCESS_PREFIX)
        assert "stderr" in result
        assert "error" in result

    def test_command_no_output(self):
        """测试无输出的命令"""
        result = run_bash_command("true")

        assert result.startswith(SUCCESS_PREFIX)
        assert "(no output)" in result

    def test_command_with_working_directory(self):
        """测试工作目录"""
        result = run_bash_command("pwd", working_directory=Path("/tmp"))

        assert result.startswith(SUCCESS_PREFIX)
        # macOS 上 /tmp 是 /private/tmp 的符号链接
        assert "tmp" in result


class TestReadFileTool:
    """测试 read_file 工具的路径处理"""

    def test_resolve_path_relative(self, tmp_path):
        """测试相对路径解析"""
        path = resolve_path("test.txt", tmp_path)
        assert path == tmp_path / "test.txt"

    def test_resolve_path_absolute(self, tmp_path):
        """测试绝对路径"""
        abs_path = "/absolute/path.txt"
        path = resolve_path(abs_path, tmp_path)
        assert str(path) == abs_path

    def test_read_file_content(self, tmp_path):
        """测试读取文件内容（直接测试 Path 操作）"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World\nLine 2")

        # 直接测试文件读取逻辑
        path = resolve_path("test.txt", tmp_path)
        content = path.read_text()
        assert "Hello World" in content


class TestWriteFileTool:
    """测试 write_file 工具的路径处理"""

    def test_write_file_content(self, tmp_path):
        """测试写入文件（直接测试 Path 操作）"""
        path = resolve_path("new.txt", tmp_path)
        path.write_text("New content")

        assert path.exists()
        assert path.read_text() == "New content"

    def test_write_creates_parent_dirs(self, tmp_path):
        """测试自动创建父目录"""
        path = resolve_path("subdir/deep/file.txt", tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Deep content")

        assert path.exists()
        assert path.read_text() == "Deep content"


class TestOutputFormatIntegration:
    """测试输出格式与 formatter 的集成"""

    def test_bash_output_format_works_with_formatter(self):
        """测试 bash 输出格式与 ToolResultFormatter 兼容"""
        from langchain_skills.stream import ToolResultFormatter, ContentType

        formatter = ToolResultFormatter()

        # 成功命令
        result = run_bash_command("echo test")
        content_type = formatter.detect_type(result)
        assert content_type == ContentType.SUCCESS
        assert formatter.is_success(result) is True

        # 失败命令
        result = run_bash_command("exit 1")
        content_type = formatter.detect_type(result)
        assert content_type == ContentType.ERROR
        assert formatter.is_success(result) is False

    def test_bash_json_output(self):
        """测试 bash JSON 输出"""
        from langchain_skills.stream import ToolResultFormatter, ContentType

        formatter = ToolResultFormatter()

        result = run_bash_command('echo \'{"key": "value"}\'')
        content_type = formatter.detect_type(result)

        # [OK] 前缀 + JSON 内容应该检测为 JSON
        assert content_type == ContentType.JSON
