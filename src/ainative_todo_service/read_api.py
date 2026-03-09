from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path
import re
from typing import Any

from .config import ConfigError, DataRepoConfig, RuntimeConfig, load_data_repo_config, load_runtime_config
from .doctor import build_report
from .mcp_tool_contracts import READ_TOOLS, SUPPORTED_WRITE_ACTIONS, WRITE_TOOLS


TASK_HEADERS = [
    "id",
    "title",
    "project",
    "priority",
    "created_date",
    "due_date",
    "deliverable",
    "status",
    "notes",
]
OPEN_STATUSES = {"todo", "doing", "blocked"}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
TODAY_HEADING_RE = re.compile(r"^# (\d{4}-\d{2}-\d{2}) 周[一二三四五六日]$", re.MULTILINE)


def _today(value: str | None) -> dt.date:
    return dt.date.today() if value is None else dt.date.fromisoformat(value)


def _parse_optional_date(value: str) -> dt.date | None:
    stripped = value.strip()
    if not stripped:
        return None
    return dt.date.fromisoformat(stripped)


def _task_summary(task: dict[str, str]) -> dict[str, str]:
    return {
        "id": task["id"],
        "title": task["title"],
        "project": task["project"],
        "priority": task["priority"],
        "created_date": task["created_date"],
        "due_date": task["due_date"],
        "deliverable": task["deliverable"],
        "status": task["status"],
        "notes": task["notes"],
    }


def _sort_open_tasks(tasks: list[dict[str, str]]) -> list[dict[str, str]]:
    def key(task: dict[str, str]) -> tuple[object, ...]:
        return (
            PRIORITY_ORDER.get(task["priority"], 99),
            _parse_optional_date(task["due_date"]) or dt.date.max,
            task["project"],
            task["id"],
        )

    return sorted(tasks, key=key)


def _load_context(config_path: Path | None, code_repo: Path | None) -> tuple[RuntimeConfig, DataRepoConfig]:
    runtime = load_runtime_config(config_path=config_path, code_repo=code_repo)
    data = load_data_repo_config(runtime.data_repo)
    return runtime, data


def _load_tasks(data_config: DataRepoConfig) -> list[dict[str, str]]:
    task_store = data_config.resolve_path("task_store")
    if not task_store.exists():
        raise ConfigError(f"Missing task file: {task_store}")

    with task_store.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        tasks: list[dict[str, str]] = []
        for row in reader:
            task = {header: (row.get(header, "") or "").strip() for header in TASK_HEADERS}
            tasks.append(task)
    return tasks


def _today_metadata(data_config: DataRepoConfig) -> dict[str, Any]:
    today_path = data_config.resolve_path("today_file")
    if not today_path.exists():
        return {
            "today_path": str(today_path),
            "today_exists": False,
            "today_archived": False,
            "today_heading_date": None,
            "markdown": "",
        }

    markdown = today_path.read_text(encoding="utf-8")
    heading = TODAY_HEADING_RE.search(markdown)
    return {
        "today_path": str(today_path),
        "today_exists": True,
        "today_archived": markdown.lstrip().startswith("# 已归档"),
        "today_heading_date": heading.group(1) if heading else None,
        "markdown": markdown,
    }


def _json_error(message: str) -> dict[str, object]:
    return {"ok": False, "error": message}


def build_doctor_payload(*, config_path: Path | None = None, code_repo: Path | None = None) -> dict[str, object]:
    try:
        payload = build_report(config_path=config_path, code_repo=code_repo or Path.cwd())
    except ConfigError as exc:
        return _json_error(str(exc))

    return payload


def build_overview_payload(
    *,
    date: str | None = None,
    config_path: Path | None = None,
    code_repo: Path | None = None,
) -> dict[str, object]:
    try:
        anchor = _today(date)
        runtime_config, data_config = _load_context(config_path, code_repo)
        tasks = _load_tasks(data_config)
        today_metadata = _today_metadata(data_config)
    except (ConfigError, ValueError) as exc:
        return _json_error(str(exc))

    open_tasks = [task for task in tasks if task["status"] in OPEN_STATUSES]
    must_do = [
        _task_summary(task)
        for task in _sort_open_tasks(open_tasks)
        if task["status"] == "doing"
        or task["priority"] == "P0"
        or ((_parse_optional_date(task["due_date"]) or dt.date.max) <= anchor)
    ]
    blocked = [_task_summary(task) for task in tasks if task["status"] == "blocked"]
    overdue = [
        _task_summary(task)
        for task in _sort_open_tasks(open_tasks)
        if (due := _parse_optional_date(task["due_date"])) is not None and due < anchor
    ]
    doing = [_task_summary(task) for task in tasks if task["status"] == "doing"]

    return {
        "ok": True,
        "date": anchor.isoformat(),
        "today_exists": today_metadata["today_exists"],
        "today_archived": today_metadata["today_archived"],
        "today_heading_date": today_metadata["today_heading_date"],
        "today_path": today_metadata["today_path"],
        "must_do": must_do,
        "must_do_count": len(must_do),
        "blocked": blocked,
        "overdue": overdue,
        "doing": doing,
        "open_count": len(open_tasks),
        "data_repo": str(runtime_config.data_repo),
        "data_config_path": str(data_config.path),
        "project_codes": sorted(data_config.projects.keys()),
    }


def build_today_markdown_payload(
    *,
    config_path: Path | None = None,
    code_repo: Path | None = None,
) -> dict[str, object]:
    try:
        _, data_config = _load_context(config_path, code_repo)
        today_metadata = _today_metadata(data_config)
    except ConfigError as exc:
        return _json_error(str(exc))

    return {
        "ok": True,
        "today_exists": today_metadata["today_exists"],
        "today_archived": today_metadata["today_archived"],
        "today_heading_date": today_metadata["today_heading_date"],
        "today_path": today_metadata["today_path"],
        "markdown": today_metadata["markdown"],
    }


def search_tasks_payload(
    *,
    query: str | None = None,
    project: str | None = None,
    status: list[str] | None = None,
    priority: list[str] | None = None,
    due_before: str | None = None,
    due_after: str | None = None,
    created_before: str | None = None,
    created_after: str | None = None,
    limit: int = 10,
    config_path: Path | None = None,
    code_repo: Path | None = None,
) -> dict[str, object]:
    try:
        _, data_config = _load_context(config_path, code_repo)
        tasks = _load_tasks(data_config)
        due_before_date = _parse_optional_date(due_before or "")
        due_after_date = _parse_optional_date(due_after or "")
        created_before_date = _parse_optional_date(created_before or "")
        created_after_date = _parse_optional_date(created_after or "")
    except (ConfigError, ValueError) as exc:
        return _json_error(str(exc))

    normalized_query = (query or "").strip().lower()
    normalized_status = {item.strip() for item in status or []}
    normalized_priority = {item.strip() for item in priority or []}
    bounded_limit = max(1, min(limit, 100))

    matches: list[dict[str, str]] = []
    for task in tasks:
        if normalized_query:
            haystack = " ".join([task["id"], task["title"], task["deliverable"], task["notes"]]).lower()
            if normalized_query not in haystack:
                continue
        if project and task["project"] != project:
            continue
        if normalized_status and task["status"] not in normalized_status:
            continue
        if normalized_priority and task["priority"] not in normalized_priority:
            continue

        due_date = _parse_optional_date(task["due_date"])
        created_date = dt.date.fromisoformat(task["created_date"])
        if due_before_date is not None and (due_date is None or due_date > due_before_date):
            continue
        if due_after_date is not None and (due_date is None or due_date < due_after_date):
            continue
        if created_before_date is not None and created_date > created_before_date:
            continue
        if created_after_date is not None and created_date < created_after_date:
            continue

        matches.append(_task_summary(task))

    sorted_matches = sorted(
        matches,
        key=lambda task: (
            PRIORITY_ORDER.get(task["priority"], 99),
            _parse_optional_date(task["due_date"]) or dt.date.max,
            task["project"],
            task["id"],
        ),
    )
    return {
        "ok": True,
        "query": query or "",
        "matches": sorted_matches[:bounded_limit],
        "count": len(sorted_matches[:bounded_limit]),
        "total_matches": len(sorted_matches),
    }


def format_tool_payload(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def doctor_capabilities() -> dict[str, object]:
    return {
        "supported_read_tools": list(READ_TOOLS),
        "supported_write_tools": list(WRITE_TOOLS),
        "supported_actions": list(SUPPORTED_WRITE_ACTIONS),
        "mcp_server_module": "ainative_todo_service.mcp_server",
    }
