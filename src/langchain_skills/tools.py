"""
LangChain Tools 定义

使用 LangChain 1.0 的 @tool 装饰器和 ToolRuntime 定义工具：
- load_skill: 加载 Skill 详细指令（Level 2）
- bash: 执行命令/脚本（Level 3）
- read_file: 读取文件

ToolRuntime 提供访问运行时信息的统一接口：
- state: 可变的执行状态
- context: 不可变的配置（如 skill_loader）
"""

import subprocess
from pathlib import Path
from dataclasses import dataclass, field

from langchain.tools import tool, ToolRuntime

from .skill_loader import SkillLoader
from .stream import resolve_path


@dataclass
class SkillAgentContext:
    """
    Agent 运行时上下文

    通过 ToolRuntime[SkillAgentContext] 在 tool 中访问
    """
    skill_loader: SkillLoader
    working_directory: Path = field(default_factory=Path.cwd)


@tool
def load_skill(skill_name: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    Load a skill's detailed instructions.

    This tool reads the SKILL.md file for the specified skill and returns
    its complete instructions. Use this when the user's request matches
    a skill's description from the available skills list.

    The skill's instructions will guide you on how to complete the task,
    which may include running scripts via the bash tool.

    Args:
        skill_name: Name of the skill to load (e.g., 'news-extractor')
    """
    loader = runtime.context.skill_loader

    # 尝试加载 skill
    skill_content = loader.load_skill(skill_name)

    if not skill_content:
        # 列出可用的 skills（从已扫描的元数据中获取）
        skills = loader.scan_skills()
        if skills:
            available = [s.name for s in skills]
            return f"Skill '{skill_name}' not found. Available skills: {', '.join(available)}"
        else:
            return f"Skill '{skill_name}' not found. No skills are currently available."

    # 获取 skill 路径信息
    skill_path = skill_content.metadata.skill_path
    scripts_dir = skill_path / "scripts"

    # 构建路径信息
    path_info = f"""
## Skill Path Info

- **Skill Directory**: `{skill_path}`
- **Scripts Directory**: `{scripts_dir}`

**Important**: When running scripts, use absolute paths like:
```bash
uv run {scripts_dir}/script_name.py [args]
```
"""

    # 返回 instructions 和路径信息
    return f"""# Skill: {skill_name}

## Instructions

{skill_content.instructions}
{path_info}
"""


@tool
def bash(command: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    Execute a bash command.

    Use this for:
    - Running skill scripts (e.g., `uv run path/to/script.py args`)
    - Installing dependencies
    - File operations
    - Any shell command

    Important for Skills:
    - Script code does NOT enter the context, only the output does
    - This is Level 3 of the Skills loading mechanism
    - Follow the skill's instructions for exact command syntax

    Args:
        command: The bash command to execute
    """
    cwd = str(runtime.context.working_directory)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 分钟超时
        )

        parts = []

        # 状态标记（与 ToolResultFormatter 配合）
        if result.returncode == 0:
            parts.append("[OK]")
        else:
            parts.append(f"[FAILED] Exit code: {result.returncode}")

        parts.append("")  # 空行分隔

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


@tool
def read_file(file_path: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    Read the contents of a file.

    Use this to:
    - Read skill documentation files
    - View script output files
    - Inspect any text file

    Args:
        file_path: Path to the file (absolute or relative to working directory)
    """
    path = resolve_path(file_path, runtime.context.working_directory)

    if not path.exists():
        return f"[Error] File not found: {file_path}"

    if not path.is_file():
        return f"[Error] Not a file: {file_path}"

    try:
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # 添加行号
        numbered_lines = []
        for i, line in enumerate(lines[:2000], 1):  # 限制行数
            numbered_lines.append(f"{i:4d}| {line}")

        if len(lines) > 2000:
            numbered_lines.append(f"... ({len(lines) - 2000} more lines)")

        return "\n".join(numbered_lines)

    except UnicodeDecodeError:
        return f"[Error] Cannot read file (binary or unknown encoding): {file_path}"
    except Exception as e:
        return f"[Error] Failed to read file: {str(e)}"


@tool
def write_file(file_path: str, content: str, runtime: ToolRuntime[SkillAgentContext]) -> str:
    """
    Write content to a file.

    Use this to:
    - Save generated content
    - Create new files
    - Modify existing files

    Args:
        file_path: Path to the file (absolute or relative to working directory)
        content: Content to write to the file
    """
    path = resolve_path(file_path, runtime.context.working_directory)

    try:
        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding="utf-8")
        return f"[Success] File written: {path}"

    except Exception as e:
        return f"[Error] Failed to write file: {str(e)}"


# 导出所有工具
# 注意：不需要 list_skills 工具，因为 skills 列表已在 system prompt 中注入
ALL_TOOLS = [load_skill, bash, read_file, write_file]
