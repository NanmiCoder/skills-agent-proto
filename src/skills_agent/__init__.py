"""
Skills Agent - 能够发现和使用 Skills 的 Coding Agent

使用 Claude Agent SDK 构建，通过正确配置 setting_sources 和 allowed_tools，
让 Claude 能够自动发现和使用 ~/.claude/skills/ 和 .claude/skills/ 中的 Skills。
"""

from skills_agent.agent import SkillsAgent

__version__ = "0.1.0"
__all__ = ["SkillsAgent"]
