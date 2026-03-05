# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CSV-based task management system (Chinese language) that generates daily execution views, project pages, and periodic reports (weekly/monthly/quarterly/half-year). Not a code project — it's a personal/team productivity system operated via CLI + AI agent.

## Key Commands

```bash
# Generate today's work view
python3 scripts/todo_workflow.py generate-today [--date YYYY-MM-DD]

# Archive today.md and sync status back to CSV
python3 scripts/todo_workflow.py close-day [--date YYYY-MM-DD]

# Generate periodic reports
python3 scripts/todo_workflow.py generate-weekly [--date YYYY-MM-DD]
python3 scripts/todo_workflow.py generate-monthly [--date YYYY-MM-DD]
python3 scripts/todo_workflow.py generate-quarterly [--date YYYY-MM-DD]
python3 scripts/todo_workflow.py generate-halfyear [--date YYYY-MM-DD]

# Rebuild all project pages
python3 scripts/todo_workflow.py generate-projects

# Run tests
python3 -m pytest tests/
```

## Architecture

- **`data/tasks.csv`** — Single source of truth for all tasks. Fields: `id, title, project, priority, created_date, due_date, deliverable, status, notes`
- **`today.md`** — Daily execution view, regenerated each morning, archived at end of day. Only `status` and `notes` fields may be modified here; other fields are immutable and validated against CSV on close-day.
- **`daily/YYYY-MM/WXX/YYYY-MM-DD.md`** — Archived daily files + summary reports
- **`projects/*.md`** — Auto-generated project pages (do not edit manually)
- **`scripts/todo_workflow.py`** — All workflow logic in a single Python script (~970 lines). No external dependencies beyond stdlib.
- **`skills/todo-workflow/`** — Claude Code skill with scene-based reference docs (morning/during-day/close-day/review)
- **`reports/templates/`** — Report templates for weekly/monthly/quarterly/half-year

## Data Contracts

- **Valid statuses**: `todo`, `doing`, `blocked`, `done`, `cancelled`
- **Valid priorities**: `P0`, `P1`, `P2`, `P3`
- **Project codes**: `UTC` (unit test client), `HYP` (half-year plan), `TAR` (team arrangement), `HYE` (Hunyuan evaluation), `AGE` (agent evaluation), `MISC` (miscellaneous)
- **Task ID format**: `{PROJECT}-{YYYYMMDD}-{NN}` (e.g., `UTC-20260304-01`)

## Skills

When the user mentions "开工", "收工", "任务更新", "生成报告", or wants to operate on today.md / tasks.csv, load `skills/todo-workflow/SKILL.md` and follow its routing instructions.

## Important Rules

- Never add fallback/safety-net measures — expose errors directly for the user to fix
- Any operation that might conflict with user instructions must be surfaced for confirmation

# currentDate
Today's date is 2026-03-05.
