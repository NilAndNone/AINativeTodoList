from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from itertools import count
from pathlib import Path
from typing import Any, Callable

import scripts.todo_workflow as workflow

from .config import ConfigError, load_runtime_config
from .contracts import CommandResult, PreviewResult
from .mcp_tool_contracts import SUPPORTED_WRITE_ACTIONS
from .operations import (
    OperationError,
    apply_close_day,
    apply_generate_projects,
    apply_generate_report,
    apply_generate_today,
    preview_close_day,
    preview_generate_projects,
    preview_generate_report,
    preview_generate_today,
)
from .preview_runner import run_preview


REPORT_TYPES = frozenset({"weekly", "monthly", "quarterly", "halfyear"})
EDITABLE_FIELDS = frozenset({"title", "project", "priority", "due_date", "deliverable", "status", "notes"})
TODAY_SECTION_HEADERS = {
    "今日必须完成": workflow.TODAY_TASK_HEADERS,
    "今日计划（非必须）": workflow.TODAY_TASK_HEADERS,
    "临时新增": workflow.ADHOC_HEADERS,
    "实际完成": workflow.COMPLETED_HEADERS,
    "未完成 & 原因": workflow.INCOMPLETE_HEADERS,
}
TODAY_FIELD_MAP = {
    "ID": "id",
    "标题": "title",
    "项目": "project",
    "P": "priority",
    "创建": "created_date",
    "DDL": "due_date",
    "产出": "deliverable",
    "状态": "status",
    "备注": "notes",
}
FIELD_LABELS = {
    "title": "标题",
    "project": "项目",
    "priority": "优先级",
    "due_date": "DDL",
    "deliverable": "产出",
    "status": "状态",
    "notes": "备注",
}


class WriteActionError(RuntimeError):
    pass


@dataclass
class PendingOperation:
    action: str
    operation_id: str
    summary: str
    files_changed: tuple[str, ...]
    apply_fn: Callable[[], CommandResult]


class WritePlanner:
    def __init__(self, *, config_path: Path | None = None, code_repo: Path | None = None) -> None:
        self._config_path = config_path
        self._code_repo = (code_repo or Path.cwd()).resolve()
        self._pending: dict[str, PendingOperation] = {}
        self._counter = count(1)

    def plan_write(self, *, action: str, args: dict[str, Any] | None = None) -> dict[str, object]:
        if action not in SUPPORTED_WRITE_ACTIONS:
            return self._error_payload(action, f"Unsupported action: {action}")

        normalized_args = args or {}
        try:
            if action == "start_day":
                return self._plan_start_day(normalized_args)
            if action == "update_task":
                return self._plan_update_task(normalized_args)
            if action == "add_task":
                return self._plan_add_task(normalized_args)
            if action == "mark_done":
                return self._plan_status_action(action, normalized_args, status="done")
            if action == "mark_blocked":
                return self._plan_status_action(action, normalized_args, status="blocked")
            if action == "unblock_task":
                return self._plan_status_action(action, normalized_args, status=str(normalized_args.get("status") or "todo").strip())
            if action == "change_priority":
                return self._plan_change_priority(normalized_args)
            if action == "change_due_date":
                return self._plan_change_due_date(normalized_args)
            if action == "cancel_task":
                return self._plan_status_action(action, normalized_args, status="cancelled")
            if action == "close_day":
                return self._plan_close_day(normalized_args)
            if action == "generate_report":
                return self._plan_generate_report(normalized_args)
            if action == "rebuild_projects":
                return self._plan_rebuild_projects()
        except (ConfigError, OperationError, ValueError, TypeError, WriteActionError, workflow.WorkflowError) as exc:
            return self._error_payload(action, str(exc))

        return self._error_payload(action, f"Unsupported action: {action}")

    def apply(self, *, operation_id: str) -> dict[str, object]:
        pending = self._pending.get(operation_id)
        if pending is None:
            return {"ok": False, "error": f"Unknown operation_id: {operation_id}"}

        try:
            result = pending.apply_fn()
        except (ConfigError, OperationError, ValueError, TypeError, WriteActionError, workflow.WorkflowError) as exc:
            return {
                "ok": False,
                "action": pending.action,
                "operation_id": operation_id,
                "error": str(exc),
            }

        self._pending.pop(operation_id, None)
        return {
            "ok": result.ok,
            "action": pending.action,
            "operation_id": operation_id,
            "applied_files": list(pending.files_changed),
            "post_summary": pending.summary,
        }

    def _plan_start_day(self, args: dict[str, Any]) -> dict[str, object]:
        runtime_config = load_runtime_config(config_path=self._config_path, code_repo=self._code_repo)
        today_file = workflow.today_path(runtime_config.data_repo)
        overwrite = bool(args.get("overwrite_unarchived_today", False))
        if today_file.exists():
            today_text = today_file.read_text(encoding="utf-8")
            if today_text.strip() and not today_text.lstrip().startswith("# 已归档") and not overwrite:
                return self._needs_input_payload(
                    "start_day",
                    [
                        {
                            "field": "overwrite_unarchived_today",
                            "prompt": "当前 today.md 尚未归档。如需覆盖生成，请确认并传入 overwrite_unarchived_today=true。",
                        }
                    ],
                )

        date = self._optional_str(args.get("date"))
        preview = preview_generate_today(code_repo=self._code_repo, data_repo=runtime_config.data_repo, date=date)
        summary = f"生成 {date or '今天'} 的 today.md。"
        return self._payload_from_preview(
            action="start_day",
            summary=summary,
            preview=preview,
            apply_fn=lambda: apply_generate_today(
                code_repo=self._code_repo,
                data_repo=runtime_config.data_repo,
                date=date,
            ),
        )

    def _plan_update_task(self, args: dict[str, Any]) -> dict[str, object]:
        action_name = self._optional_str(args.get("_action_override")) or "update_task"
        selector = args.get("task_selector")
        if not isinstance(selector, dict):
            return self._needs_input_payload(
                action_name,
                [
                    {
                        "field": "task_selector",
                        "prompt": "请提供任务 ID，或提供能唯一定位任务的 query/project/status 条件。",
                    }
                ],
            )

        patch = self._normalize_patch(args.get("patch"))
        if patch is None:
            return self._needs_input_payload(
                action_name,
                [{"field": "patch", "prompt": "请说明需要更新哪些字段。"}],
            )

        runtime_config = load_runtime_config(config_path=self._config_path, code_repo=self._code_repo)
        tasks = workflow.load_tasks(runtime_config.data_repo)
        resolved = self._resolve_task(action_name, selector, tasks)
        if resolved["status"] != "ok":
            return resolved["payload"]

        task = resolved["task"]
        assert isinstance(task, dict)
        summary = f"更新任务 {task['id']}：{self._patch_summary(patch)}。"
        preview = self._preview_local_write(
            runtime_config.data_repo,
            summary,
            lambda root: self._mutate_existing_task(root, task["id"], patch),
        )
        return self._payload_from_preview(
            action=action_name,
            summary=summary,
            preview=preview,
            apply_fn=lambda: self._apply_local_write(
                runtime_config.data_repo,
                f"update_task:{task['id']}",
                lambda root: self._mutate_existing_task(root, task["id"], patch),
            ),
        )

    def _plan_add_task(self, args: dict[str, Any]) -> dict[str, object]:
        missing = self._missing_add_task_fields(args)
        if missing:
            return self._needs_input_payload("add_task", missing)

        runtime_config = load_runtime_config(config_path=self._config_path, code_repo=self._code_repo)
        tasks = workflow.load_tasks(runtime_config.data_repo)
        new_task = self._build_new_task(tasks, args)
        summary = f"新增任务 {new_task['id']}：{new_task['title']}。"
        preview = self._preview_local_write(
            runtime_config.data_repo,
            summary,
            lambda root: self._mutate_add_task(root, new_task),
        )
        return self._payload_from_preview(
            action="add_task",
            summary=summary,
            preview=preview,
            apply_fn=lambda: self._apply_local_write(
                runtime_config.data_repo,
                f"add_task:{new_task['id']}",
                lambda root: self._mutate_add_task(root, new_task),
            ),
        )

    def _plan_status_action(self, action: str, args: dict[str, Any], *, status: str) -> dict[str, object]:
        selector = args.get("task_selector")
        if not isinstance(selector, dict):
            return self._needs_input_payload(
                action,
                [
                    {
                        "field": "task_selector",
                        "prompt": "请提供任务 ID，或提供能唯一定位任务的 query/project/status 条件。",
                    }
                ],
            )

        patch: dict[str, str] = {"status": status}
        if "notes" in args:
            patch["notes"] = self._string_value(args.get("notes"))
        return self._plan_update_task({"task_selector": selector, "patch": patch} | {"_action_override": action})

    def _plan_change_priority(self, args: dict[str, Any]) -> dict[str, object]:
        if "priority" not in args:
            return self._needs_input_payload(
                "change_priority",
                [{"field": "priority", "prompt": "请提供新的优先级，值为 P0 / P1 / P2 / P3。"}],
            )
        patch = {"priority": self._string_value(args.get("priority"))}
        if "notes" in args:
            patch["notes"] = self._string_value(args.get("notes"))
        return self._plan_update_task({"task_selector": args.get("task_selector"), "patch": patch} | {"_action_override": "change_priority"})

    def _plan_change_due_date(self, args: dict[str, Any]) -> dict[str, object]:
        if bool(args.get("clear")):
            due_date = ""
        elif "due_date" in args:
            due_date = self._string_value(args.get("due_date"))
        else:
            return self._needs_input_payload(
                "change_due_date",
                [{"field": "due_date", "prompt": "请提供新的 DDL（YYYY-MM-DD），或传入 clear=true 清空。"}],
            )
        patch = {"due_date": due_date}
        if "notes" in args:
            patch["notes"] = self._string_value(args.get("notes"))
        return self._plan_update_task({"task_selector": args.get("task_selector"), "patch": patch} | {"_action_override": "change_due_date"})

    def _plan_close_day(self, args: dict[str, Any]) -> dict[str, object]:
        runtime_config = load_runtime_config(config_path=self._config_path, code_repo=self._code_repo)
        date = self._optional_str(args.get("date"))
        preview = preview_close_day(code_repo=self._code_repo, data_repo=runtime_config.data_repo, date=date)
        summary = f"归档 {date or '今天'} 的 today.md，并同步 data/tasks.csv 与 projects/。"
        return self._payload_from_preview(
            action="close_day",
            summary=summary,
            preview=preview,
            apply_fn=lambda: apply_close_day(
                code_repo=self._code_repo,
                data_repo=runtime_config.data_repo,
                date=date,
            ),
        )

    def _plan_generate_report(self, args: dict[str, Any]) -> dict[str, object]:
        report_type = self._optional_str(args.get("report_type"))
        if report_type is None:
            return self._needs_input_payload(
                "generate_report",
                [
                    {
                        "field": "report_type",
                        "prompt": "请提供报表类型：weekly / monthly / quarterly / halfyear。",
                    }
                ],
            )
        if report_type not in REPORT_TYPES:
            raise WriteActionError(f"Unsupported report_type: {report_type}")

        runtime_config = load_runtime_config(config_path=self._config_path, code_repo=self._code_repo)
        date = self._optional_str(args.get("date"))
        preview = preview_generate_report(
            code_repo=self._code_repo,
            data_repo=runtime_config.data_repo,
            report_type=report_type,
            date=date,
        )
        summary = f"生成 {report_type} 报告（锚点 {date or '今天'}）。"
        return self._payload_from_preview(
            action="generate_report",
            summary=summary,
            preview=preview,
            apply_fn=lambda: apply_generate_report(
                code_repo=self._code_repo,
                data_repo=runtime_config.data_repo,
                report_type=report_type,
                date=date,
            ),
        )

    def _plan_rebuild_projects(self) -> dict[str, object]:
        runtime_config = load_runtime_config(config_path=self._config_path, code_repo=self._code_repo)
        preview = preview_generate_projects(code_repo=self._code_repo, data_repo=runtime_config.data_repo)
        summary = "重建所有项目页。"
        return self._payload_from_preview(
            action="rebuild_projects",
            summary=summary,
            preview=preview,
            apply_fn=lambda: apply_generate_projects(
                code_repo=self._code_repo,
                data_repo=runtime_config.data_repo,
            ),
        )

    def _preview_local_write(self, data_repo: Path, summary: str, mutation: Callable[[Path], None]) -> PreviewResult:
        return run_preview(
            real_root=data_repo,
            summary=summary,
            operation=lambda temp_root: self._apply_local_write(temp_root, summary, mutation, resolve_root=False),
        )

    def _apply_local_write(
        self,
        data_repo: Path,
        label: str,
        mutation: Callable[[Path], None],
        *,
        resolve_root: bool = True,
    ) -> CommandResult:
        root = data_repo.resolve() if resolve_root else data_repo
        mutation(root)
        return CommandResult(command=[label], returncode=0, stdout="", stderr="")

    def _payload_from_preview(
        self,
        *,
        action: str,
        summary: str,
        preview: PreviewResult,
        apply_fn: Callable[[], CommandResult],
    ) -> dict[str, object]:
        if not preview.ok:
            return self._error_payload(action, preview.command_result.stderr.strip() or summary)
        if not preview.changed_files:
            return {"status": "noop", "action": action, "summary": summary}

        operation_id = self._next_operation_id()
        self._pending[operation_id] = PendingOperation(
            action=action,
            operation_id=operation_id,
            summary=summary,
            files_changed=preview.changed_files,
            apply_fn=apply_fn,
        )
        return {
            "status": "ready_for_confirm",
            "action": action,
            "operation_id": operation_id,
            "summary": summary,
            "files_changed": list(preview.changed_files),
            "diffs": [{"path": entry.path, "unified_diff": entry.unified_diff} for entry in preview.diffs],
            "warnings": [],
        }

    def _resolve_task(self, action: str, selector: dict[str, Any], tasks: list[dict[str, str]]) -> dict[str, object]:
        task_id = self._optional_str(selector.get("id"))
        query = self._optional_str(selector.get("query"))
        project = self._optional_str(selector.get("project"))
        statuses = self._normalize_string_list(selector.get("status"))

        if task_id is None and query is None:
            return {
                "status": "error",
                "payload": self._needs_input_payload(
                    action,
                    [{"field": "task_selector", "prompt": "请至少提供任务 ID 或 query。"}],
                ),
            }

        matches: list[dict[str, str]] = []
        for task in tasks:
            if task_id is not None and task["id"] != task_id:
                continue
            if query is not None:
                haystack = " ".join([task["id"], task["title"], task["deliverable"], task["notes"]]).lower()
                if query.lower() not in haystack:
                    continue
            if project is not None and task["project"] != project:
                continue
            if statuses and task["status"] not in statuses:
                continue
            matches.append(task)

        if not matches:
            raise WriteActionError("No task matches the provided selector.")
        if len(matches) > 1:
            return {
                "status": "error",
                "payload": {
                    "status": "ambiguous",
                    "action": action,
                    "candidates": [
                        {
                            "id": task["id"],
                            "title": task["title"],
                            "project": task["project"],
                            "status": task["status"],
                        }
                        for task in matches[:10]
                    ],
                    "prompt": "我找到了多个候选任务，请指定 ID。",
                },
            }
        return {"status": "ok", "task": matches[0]}

    def _normalize_patch(self, payload: Any) -> dict[str, str] | None:
        if payload is None:
            return None
        if not isinstance(payload, dict):
            raise WriteActionError("patch must be an object")

        patch: dict[str, str] = {}
        for field, value in payload.items():
            if field.startswith("_"):
                continue
            if field not in EDITABLE_FIELDS:
                raise WriteActionError(f"Unsupported patch field: {field}")
            patch[field] = self._string_value(value)
        return patch or None

    def _mutate_existing_task(self, root: Path, task_id: str, patch: dict[str, str]) -> None:
        tasks = workflow.load_tasks(root)
        matched = False
        for index, task in enumerate(tasks):
            if task["id"] != task_id:
                continue
            updated = dict(task)
            updated.update(patch)
            workflow.validate_task(updated)
            tasks[index] = updated
            matched = True
            break
        if not matched:
            raise WriteActionError(f"Unknown task id: {task_id}")

        workflow.save_tasks(root, tasks)
        self._update_today_task(root, updated)

    def _missing_add_task_fields(self, args: dict[str, Any]) -> list[dict[str, str]]:
        prompts = {
            "title": "这个新任务的标题是什么？",
            "project": "这个新任务属于哪个项目代码？",
            "priority": "这个新任务的优先级是 P0 / P1 / P2 / P3 哪一个？",
            "deliverable": "这个任务的预期产出是什么？",
            "status": "这个任务当前状态是 todo / doing / blocked / done / cancelled 哪一个？",
        }
        missing: list[dict[str, str]] = []
        for field, prompt in prompts.items():
            value = args.get(field)
            if value is None or str(value).strip() == "":
                missing.append({"field": field, "prompt": prompt})
        return missing

    def _build_new_task(self, tasks: list[dict[str, str]], args: dict[str, Any]) -> dict[str, str]:
        created_date = self._optional_str(args.get("created_date")) or self._optional_str(args.get("date")) or dt.date.today().isoformat()
        project = self._string_value(args.get("project"))
        task_id = self._optional_str(args.get("id")) or workflow.next_task_id(tasks, project, created_date)
        if any(task["id"] == task_id for task in tasks):
            raise WriteActionError(f"Task id already exists: {task_id}")

        task = {
            "id": task_id,
            "title": self._string_value(args.get("title")),
            "project": project,
            "priority": self._string_value(args.get("priority")),
            "created_date": created_date,
            "due_date": self._string_value(args.get("due_date")),
            "deliverable": self._string_value(args.get("deliverable")),
            "status": self._string_value(args.get("status")),
            "notes": self._string_value(args.get("notes")),
        }
        workflow.validate_task(task)
        return task

    def _mutate_add_task(self, root: Path, task: dict[str, str]) -> None:
        tasks = workflow.load_tasks(root)
        if any(item["id"] == task["id"] for item in tasks):
            raise WriteActionError(f"Task id already exists: {task['id']}")
        tasks.append(dict(task))
        workflow.save_tasks(root, tasks)
        self._insert_task_into_today(root, task)

    def _load_active_today(self, root: Path) -> dict[str, object] | None:
        path = workflow.today_path(root)
        if not path.exists():
            return None

        text = path.read_text(encoding="utf-8")
        if text.lstrip().startswith("# 已归档"):
            return None

        anchor, sections = workflow.split_sections(text)
        parsed: dict[str, object] = {"date": anchor, "notes": sections.get("备注", "").strip()}
        for name, headers in TODAY_SECTION_HEADERS.items():
            actual_headers, rows = workflow.parse_table(sections.get(name, ""))
            if actual_headers != headers:
                raise workflow.WorkflowError(f"Section '{name}' has unexpected headers: {actual_headers}")
            parsed[name] = rows
        return parsed

    def _save_active_today(self, root: Path, parsed: dict[str, object]) -> None:
        anchor = parsed["date"]
        assert isinstance(anchor, dt.date)
        lines = [f"# {anchor.isoformat()} 周{workflow.weekday_label(anchor)}", ""]
        for name, headers in TODAY_SECTION_HEADERS.items():
            section_rows = parsed[name]
            assert isinstance(section_rows, list)
            table_rows = [[row.get(header, "") for header in headers] for row in section_rows]
            lines.extend([f"## {name}", "", workflow.render_markdown_table(headers, table_rows), ""])
        lines.extend(["## 备注", "", str(parsed.get("notes", "")), ""])
        workflow.write_text(workflow.today_path(root), "\n".join(lines))

    def _update_today_task(self, root: Path, task: dict[str, str]) -> None:
        parsed = self._load_active_today(root)
        if parsed is None:
            return

        found = False
        for section_name in ("今日必须完成", "今日计划（非必须）"):
            rows = parsed[section_name]
            assert isinstance(rows, list)
            for row in rows:
                if row.get("ID", "").strip() != task["id"]:
                    continue
                for display_name, field_name in TODAY_FIELD_MAP.items():
                    row[display_name] = task[field_name]
                found = True

        if found:
            self._save_active_today(root, parsed)

    def _insert_task_into_today(self, root: Path, task: dict[str, str]) -> None:
        parsed = self._load_active_today(root)
        if parsed is None:
            return

        anchor = parsed["date"]
        assert isinstance(anchor, dt.date)
        if task["created_date"] != anchor.isoformat():
            return

        for section_name in ("今日必须完成", "今日计划（非必须）"):
            rows = parsed[section_name]
            assert isinstance(rows, list)
            if any(row.get("ID", "").strip() == task["id"] for row in rows):
                return

        section_name = self._classify_today_section(task, anchor)
        rows = parsed[section_name]
        assert isinstance(rows, list)
        rows.append({display_name: task[field_name] for display_name, field_name in TODAY_FIELD_MAP.items()})
        self._save_active_today(root, parsed)

    def _classify_today_section(self, task: dict[str, str], anchor: dt.date) -> str:
        due_date = workflow.parse_optional_date(task["due_date"])
        if task["status"] == "doing" or task["priority"] == "P0" or (due_date is not None and due_date <= anchor):
            return "今日必须完成"
        return "今日计划（非必须）"

    def _next_operation_id(self) -> str:
        return f"op_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{next(self._counter):04d}"

    def _patch_summary(self, patch: dict[str, str]) -> str:
        parts = []
        for field, value in patch.items():
            label = FIELD_LABELS.get(field, field)
            if field == "due_date" and not value:
                parts.append(f"{label}=清空")
            else:
                parts.append(f"{label}={value or '空'}")
        return "，".join(parts)

    def _needs_input_payload(self, action: str, missing_fields: list[dict[str, str]]) -> dict[str, object]:
        return {
            "status": "needs_input",
            "action": action,
            "missing_fields": missing_fields,
        }

    def _error_payload(self, action: str, message: str) -> dict[str, object]:
        return {
            "status": "error",
            "action": action,
            "error": message,
        }

    def _optional_str(self, value: Any) -> str | None:
        text = self._string_value(value)
        return text or None

    def _string_value(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _normalize_string_list(self, value: Any) -> set[str]:
        if value is None:
            return set()
        if isinstance(value, list):
            return {str(item).strip() for item in value if str(item).strip()}
        return {str(value).strip()} if str(value).strip() else set()
