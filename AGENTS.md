# Repository Guidelines

## Project Structure & Module Organization
- `src/langchain_skills/` houses the core package (agent, CLI, tools, skill loader, and `stream/` formatting/tracking helpers).
- `tests/` contains pytest-based unit tests named `test_*.py`.
- `examples/` provides runnable demos for CLI and agent usage.
- `docs/` holds design notes and long-form explanations.
- `.claude/skills/` contains example Skills with `SKILL.md` and scripts.
- `pyproject.toml` defines dependencies and the `langchain-skills` CLI entry point; `uv.lock` pins versions.

## Build, Test, and Development Commands
- `uv sync`: install dependencies into the local environment.
- `uv run langchain-skills --interactive`: run the interactive CLI demo.
- `uv run langchain-skills "列出当前目录"`: run a single prompt.
- `uv run langchain-skills --list-skills`: verify Skills discovery.
- `uv run python -m pytest tests/ -v`: run the test suite.
- Packaging uses Hatchling via `pyproject.toml`; no separate build step is required for local development.

## Coding Style & Naming Conventions
- Python 3.12; use 4-space indentation and type hints where practical.
- Follow existing patterns: `snake_case` for modules/functions, `CamelCase` for classes.
- Keep CLI output and stream formatting behavior consistent with existing utilities in `src/langchain_skills/stream/`.

## Testing Guidelines
- Use pytest; place new tests under `tests/` with `test_*.py` naming.
- Add tests when changing tool output formatting, stream event parsing, or CLI behaviors.
- Run targeted tests locally before opening a PR.

## Commit & Pull Request Guidelines
- Commit messages follow a Conventional Commits style seen in history (e.g., `feat: add X`, `refactor: simplify Y`, `docs: update README`).
- PRs should include a short summary, test command(s) run, and screenshots or terminal output for CLI/UX changes.
- Link related issues when available.

## Configuration & Security
- Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN`; `ANTHROPIC_BASE_URL` is optional for proxies.
- Do not commit secrets; keep local credentials in `.env`.
