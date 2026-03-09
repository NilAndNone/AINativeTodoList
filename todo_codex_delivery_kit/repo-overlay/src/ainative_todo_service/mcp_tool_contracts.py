from __future__ import annotations

"""
This module is intentionally a contract file, not a production MCP server.

Its job is to pin down the final tool surface so Codex can implement the MCP
transport later without inventing ad-hoc JSON shapes on the fly.
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
