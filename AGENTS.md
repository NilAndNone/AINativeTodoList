# Repository Guidelines

## Project Structure & Module Organization
- `scripts/todo_workflow.py`: main CLI and workflow logic (single source of behavior).
- `tests/test_todo_workflow.py`: regression tests for `generate-today`, `close-day`, and report generation.
- `data/tasks.csv`: canonical task data source; all persistent task state lives here.
- `today.md`: working file for the current day (ephemeral; archived by CLI).
- `daily/YYYY-MM/WXX/`: archived daily files and generated summaries.
- `projects/*.md`: generated project views; do not treat as manual source files.
- `reports/templates/`: report templates used by summary generation.

## Build, Test, and Development Commands
- `python3 scripts/todo_workflow.py generate-today [--date YYYY-MM-DD]`: build today’s execution view.
- `python3 scripts/todo_workflow.py close-day [--date YYYY-MM-DD]`: sync updates back to CSV, archive `today.md`, rebuild project pages.
- `python3 scripts/todo_workflow.py generate-weekly|generate-monthly|generate-quarterly|generate-halfyear [--date YYYY-MM-DD]`: generate periodic reports.
- `python3 scripts/todo_workflow.py generate-projects`: regenerate all project pages from `data/tasks.csv`.
- `python3 -m pytest tests/`: run the full test suite.

## Coding Style & Naming Conventions
- Follow Python conventions: 4-space indentation, `snake_case` for functions/variables, `UPPER_CASE` for constants.
- Keep explicit type hints (existing code uses `from __future__ import annotations` and typed signatures).
- Prefer standard-library-only solutions unless a dependency is clearly justified.
- Keep Markdown/CSV field names aligned with existing data contract keys.

## Testing Guidelines
- Framework: `unittest` executed via `pytest`.
- Name files `test_*.py` and test methods `test_*`.
- Add or update tests for every behavior change in CLI commands, CSV validation, or archive/report output.
- No fixed coverage threshold is configured; prioritize meaningful path coverage over raw percentage.

## Commit & Pull Request Guidelines
- Follow observed commit style: Conventional Commit prefixes (e.g., `feat: workflow v1`, `feat: init first todo list`).
- Use focused commits (`feat:`, `fix:`, `test:`, `docs:`) with one logical change per commit.
- PRs should include: purpose, affected commands/files, test evidence (`python3 -m pytest tests/`), and sample output paths when generation behavior changes.

## Data Integrity & Safety Rules
- Treat `data/tasks.csv` as the single source of truth.
- In `today.md`, only update task `状态` and `备注` for existing rows.
- Avoid manual edits to generated artifacts under `projects/` and summary outputs; regenerate via CLI.
