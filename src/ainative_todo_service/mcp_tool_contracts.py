from __future__ import annotations

"""
Contract-only definitions for the staged MCP tool surface.

This file intentionally stays lightweight so the read/write tool names are fixed
before later stages add more behavior behind them.
"""

from dataclasses import dataclass, field
from typing import Any, Literal


PlanStatus = Literal["needs_input", "ambiguous", "ready_for_confirm", "noop", "error"]


@dataclass(frozen=True)
class MissingField:
    field: str
    prompt: str


@dataclass(frozen=True)
class CandidateTask:
    id: str
    title: str
    project: str
    status: str


@dataclass(frozen=True)
class PlannedWrite:
    status: PlanStatus
    action: str
    operation_id: str | None = None
    summary: str | None = None
    missing_fields: tuple[MissingField, ...] = ()
    candidates: tuple[CandidateTask, ...] = ()
    files_changed: tuple[str, ...] = ()
    diffs: tuple[dict[str, str], ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


READ_TOOLS = (
    "todo_doctor",
    "todo_get_overview",
    "todo_get_today_markdown",
    "todo_search_tasks",
)

WRITE_TOOLS = (
    "todo_plan_write",
    "todo_apply",
)

SUPPORTED_WRITE_ACTIONS = (
    "start_day",
    "update_task",
    "add_task",
    "mark_done",
    "mark_blocked",
    "unblock_task",
    "change_priority",
    "change_due_date",
    "cancel_task",
    "close_day",
    "generate_report",
    "rebuild_projects",
)
