#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
from collections import defaultdict
from pathlib import Path


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

TODAY_TASK_HEADERS = ["ID", "标题", "项目", "P", "创建", "DDL", "产出", "状态", "备注"]
ADHOC_HEADERS = ["标题", "项目", "P", "DDL", "产出", "状态", "备注"]
COMPLETED_HEADERS = ["ID", "标题", "完成情况"]
INCOMPLETE_HEADERS = ["ID", "标题", "原因", "后续计划"]

PROJECTS = {
    "UTC": {
        "name": "单测客户端",
        "filename": "unit-test-client.md",
        "focus": "客户端工程实现、稳定性、性能、监控与离线流程建设。",
    },
    "HYP": {
        "name": "半年工作安排",
        "filename": "half-year-plan.md",
        "focus": "未来半年的工作主线、阶段性交付节奏与整体规划口径。",
    },
    "TAR": {
        "name": "团队成员工作安排",
        "filename": "team-arrangement.md",
        "focus": "个人工作安排与团队成员承接方向的阶段性拆解。",
    },
    "HYE": {
        "name": "混元单测评测",
        "filename": "hunyuan-evaluation.md",
        "focus": "模型评测事项记录、整理与边界维护。",
    },
    "AGE": {
        "name": "单测评测",
        "filename": "agent-evaluation.md",
        "focus": "单元测试代码生成 agent 的评测框架与阶段性输出。",
    },
    "MISC": {
        "name": "杂项",
        "filename": "misc.md",
        "focus": "临时支持、会议、沟通和跨项目事项。",
    },
}

OPEN_STATUSES = {"todo", "doing", "blocked"}
VALID_STATUSES = OPEN_STATUSES | {"done", "cancelled"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
WEEKDAY_LABELS = "一二三四五六日"


class WorkflowError(RuntimeError):
    pass


def repo_root_from(script_path: Path) -> Path:
    return script_path.resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Task workflow CLI")
    parser.add_argument(
        "--root",
        type=Path,
        default=repo_root_from(Path(__file__)),
        help=argparse.SUPPRESS,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("generate-today", "close-day", "generate-weekly", "generate-monthly", "generate-quarterly", "generate-halfyear", "generate-projects"):
        sub = subparsers.add_parser(name)
        if name != "generate-projects":
            sub.add_argument("--date", dest="date", help="Anchor date in YYYY-MM-DD format")

    return parser.parse_args()


def today_date(value: str | None) -> dt.date:
    if not value:
        return dt.date.today()
    return dt.date.fromisoformat(value)


def weekday_label(day: dt.date) -> str:
    return WEEKDAY_LABELS[day.weekday()]


def iso_week_folder(day: dt.date) -> str:
    return f"W{day.isocalendar().week:02d}"


def task_csv_path(root: Path) -> Path:
    return root / "data" / "tasks.csv"


def today_path(root: Path) -> Path:
    return root / "today.md"


def daily_path_for(root: Path, day: dt.date) -> Path:
    return root / "daily" / day.strftime("%Y-%m") / iso_week_folder(day) / f"{day.isoformat()}.md"


def weekly_summary_path(root: Path, day: dt.date) -> Path:
    return root / "daily" / day.strftime("%Y-%m") / iso_week_folder(day) / "weekly-summary.md"


def monthly_summary_path(root: Path, day: dt.date) -> Path:
    return root / "daily" / day.strftime("%Y-%m") / "monthly-summary.md"


def quarter_summary_path(root: Path, day: dt.date) -> Path:
    quarter = ((day.month - 1) // 3) + 1
    return root / "daily" / f"{day.year}-Q{quarter}-summary.md"


def halfyear_summary_path(root: Path, day: dt.date) -> Path:
    half = 1 if day.month <= 6 else 2
    return root / "daily" / f"{day.year}-H{half}-summary.md"


def safe_cell(value: str) -> str:
    return value.replace("|", "/").strip()


def parse_optional_date(value: str) -> dt.date | None:
    value = value.strip()
    if not value:
        return None
    return dt.date.fromisoformat(value)


def validate_task(task: dict[str, str]) -> None:
    missing = [header for header in TASK_HEADERS if header not in task]
    if missing:
        raise WorkflowError(f"Task missing fields: {missing}")
    if not task["id"]:
        raise WorkflowError("Task id cannot be empty")
    if task["project"] not in PROJECTS:
        raise WorkflowError(f"Unknown project: {task['project']}")
    if task["priority"] not in VALID_PRIORITIES:
        raise WorkflowError(f"Unknown priority: {task['priority']}")
    if task["status"] not in VALID_STATUSES:
        raise WorkflowError(f"Unknown status: {task['status']}")
    dt.date.fromisoformat(task["created_date"])
    parse_optional_date(task["due_date"])


def load_tasks(root: Path) -> list[dict[str, str]]:
    path = task_csv_path(root)
    if not path.exists():
        raise WorkflowError(f"Missing task file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        tasks = []
        for row in reader:
            task = {header: (row.get(header, "") or "").strip() for header in TASK_HEADERS}
            validate_task(task)
            tasks.append(task)
    return tasks


def save_tasks(root: Path, tasks: list[dict[str, str]]) -> None:
    path = task_csv_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TASK_HEADERS)
        writer.writeheader()
        for task in tasks:
            validate_task(task)
            writer.writerow(task)


def sort_open_tasks(tasks: list[dict[str, str]]) -> list[dict[str, str]]:
    def key(task: dict[str, str]) -> tuple[object, ...]:
        due = parse_optional_date(task["due_date"])
        return (
            PRIORITY_ORDER[task["priority"]],
            due or dt.date.max,
            task["project"],
            task["id"],
        )

    return sorted(tasks, key=key)


def render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        rows = [["" for _ in headers]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        padded = row + [""] * (len(headers) - len(row))
        cells = [safe_cell(value) for value in padded[: len(headers)]]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def task_row(task: dict[str, str]) -> list[str]:
    return [
        task["id"],
        task["title"],
        task["project"],
        task["priority"],
        task["created_date"],
        task["due_date"],
        task["deliverable"],
        task["status"],
        task["notes"],
    ]


def render_today(root: Path, anchor: dt.date) -> str:
    tasks = load_tasks(root)
    open_tasks = [task for task in tasks if task["status"] in OPEN_STATUSES]
    must_rows = []
    plan_rows = []
    for task in sort_open_tasks(open_tasks):
        due = parse_optional_date(task["due_date"])
        is_must = task["status"] == "doing" or task["priority"] == "P0" or (due is not None and due <= anchor)
        if is_must:
            must_rows.append(task_row(task))
        else:
            plan_rows.append(task_row(task))

    lines = [
        f"# {anchor.isoformat()} 周{weekday_label(anchor)}",
        "",
        "## 今日必须完成",
        "",
        render_markdown_table(TODAY_TASK_HEADERS, must_rows),
        "",
        "## 今日计划（非必须）",
        "",
        render_markdown_table(TODAY_TASK_HEADERS, plan_rows),
        "",
        "## 临时新增",
        "",
        render_markdown_table(ADHOC_HEADERS, []),
        "",
        "## 实际完成",
        "",
        render_markdown_table(COMPLETED_HEADERS, []),
        "",
        "## 未完成 & 原因",
        "",
        render_markdown_table(INCOMPLETE_HEADERS, []),
        "",
        "## 备注",
        "",
        "补充当天的上下文、决策和临时信息。",
        "",
    ]
    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def split_sections(text: str) -> tuple[dt.date, dict[str, str]]:
    heading = re.search(r"^# (\d{4}-\d{2}-\d{2}) 周[一二三四五六日]$", text, re.MULTILINE)
    if not heading:
        raise WorkflowError("today.md is missing the expected date heading")
    anchor = dt.date.fromisoformat(heading.group(1))
    sections: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return anchor, {name: "\n".join(lines).strip("\n") for name, lines in sections.items()}


def parse_table(section_body: str) -> tuple[list[str], list[dict[str, str]]]:
    lines = [line.strip() for line in section_body.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return [], []
    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        cells.extend([""] * (len(headers) - len(cells)))
        row = {header: cells[index] for index, header in enumerate(headers)}
        if any(value for value in row.values()):
            rows.append(row)
    return headers, rows


def parse_today_file(root: Path) -> dict[str, object]:
    path = today_path(root)
    text = path.read_text(encoding="utf-8")
    anchor, sections = split_sections(text)

    expected = {
        "今日必须完成": TODAY_TASK_HEADERS,
        "今日计划（非必须）": TODAY_TASK_HEADERS,
        "临时新增": ADHOC_HEADERS,
        "实际完成": COMPLETED_HEADERS,
        "未完成 & 原因": INCOMPLETE_HEADERS,
    }
    parsed: dict[str, object] = {"date": anchor, "notes": sections.get("备注", "").strip()}
    for name, headers in expected.items():
        actual_headers, rows = parse_table(sections.get(name, ""))
        if actual_headers != headers:
            raise WorkflowError(f"Section '{name}' has unexpected headers: {actual_headers}")
        parsed[name] = rows
    return parsed


def next_task_id(tasks: list[dict[str, str]], project: str, created_date: str) -> str:
    prefix = f"{project}-{created_date.replace('-', '')}-"
    current = 0
    for task in tasks:
        if task["id"].startswith(prefix):
            try:
                current = max(current, int(task["id"].rsplit("-", 1)[1]))
            except ValueError:
                continue
    return f"{prefix}{current + 1:02d}"


def compare_immutable_fields(task: dict[str, str], row: dict[str, str]) -> None:
    field_map = {
        "标题": "title",
        "项目": "project",
        "P": "priority",
        "创建": "created_date",
        "DDL": "due_date",
        "产出": "deliverable",
    }
    for display_name, field_name in field_map.items():
        row_value = row.get(display_name, "")
        task_value = task[field_name]
        if row_value != task_value:
            raise WorkflowError(
                f"Task {task['id']} changed immutable field '{display_name}' from '{task_value}' to '{row_value}'"
            )


def resolve_completion_targets(
    rows: list[dict[str, str]],
    id_to_task: dict[str, dict[str, str]],
    title_to_ids: dict[str, list[str]],
) -> list[dict[str, str]]:
    resolved = []
    for row in rows:
        task_id = row.get("ID", "").strip()
        title = row.get("标题", "").strip()
        if task_id:
            task = id_to_task.get(task_id)
            if task is None:
                raise WorkflowError(f"Completion row references unknown task id: {task_id}")
            resolved.append(task)
            continue
        if title and len(title_to_ids.get(title, [])) == 1:
            resolved.append(id_to_task[title_to_ids[title][0]])
            continue
        if title:
            raise WorkflowError(f"Completion row cannot be resolved uniquely: {title}")
    return resolved


def sync_today(root: Path) -> tuple[dt.date, Path]:
    parsed = parse_today_file(root)
    anchor = parsed["date"]
    assert isinstance(anchor, dt.date)
    tasks = load_tasks(root)
    id_to_task = {task["id"]: task for task in tasks}

    for section_name in ("今日必须完成", "今日计划（非必须）"):
        rows = parsed[section_name]
        assert isinstance(rows, list)
        for row in rows:
            task_id = row["ID"]
            task = id_to_task.get(task_id)
            if task is None:
                raise WorkflowError(f"{section_name} references unknown task id: {task_id}")
            compare_immutable_fields(task, row)
            status = row["状态"]
            if status not in VALID_STATUSES:
                raise WorkflowError(f"Task {task_id} has invalid status: {status}")
            task["status"] = status
            task["notes"] = row["备注"]

    adhoc_rows = parsed["临时新增"]
    assert isinstance(adhoc_rows, list)
    new_tasks: list[dict[str, str]] = []
    for row in adhoc_rows:
        project = row["项目"]
        priority = row["P"]
        status = row["状态"]
        if project not in PROJECTS:
            raise WorkflowError(f"Ad hoc task has unknown project: {project}")
        if priority not in VALID_PRIORITIES:
            raise WorkflowError(f"Ad hoc task has invalid priority: {priority}")
        if status not in VALID_STATUSES:
            raise WorkflowError(f"Ad hoc task has invalid status: {status}")
        task = {
            "id": next_task_id(tasks + new_tasks, project, anchor.isoformat()),
            "title": row["标题"],
            "project": project,
            "priority": priority,
            "created_date": anchor.isoformat(),
            "due_date": row["DDL"],
            "deliverable": row["产出"],
            "status": status,
            "notes": row["备注"],
        }
        if not task["title"]:
            raise WorkflowError("Ad hoc task title cannot be empty")
        validate_task(task)
        new_tasks.append(task)

    tasks.extend(new_tasks)
    id_to_task = {task["id"]: task for task in tasks}
    title_to_ids: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        title_to_ids[task["title"]].append(task["id"])

    completed_rows = parsed["实际完成"]
    assert isinstance(completed_rows, list)
    for task in resolve_completion_targets(completed_rows, id_to_task, title_to_ids):
        task["status"] = "done"

    save_tasks(root, tasks)

    archive_path = daily_path_for(root, anchor)
    write_text(archive_path, today_path(root).read_text(encoding="utf-8"))
    write_text(
        today_path(root),
        "\n".join(
            [
                "# 已归档",
                "",
                f"`today.md` 已归档到 `{archive_path.relative_to(root)}`。",
                "",
                "运行 `python3 scripts/todo_workflow.py generate-today` 生成新的每日工作文件。",
                "",
            ]
        ),
    )
    return anchor, archive_path


def collect_daily_records(root: Path, start: dt.date | None = None, end: dt.date | None = None) -> list[dict[str, object]]:
    daily_root = root / "daily"
    if not daily_root.exists():
        return []
    records = []
    for path in sorted(daily_root.rglob("*.md")):
        if path.name.endswith("summary.md"):
            continue
        match = re.match(r"(\d{4}-\d{2}-\d{2})\.md$", path.name)
        if not match:
            continue
        day = dt.date.fromisoformat(match.group(1))
        if start and day < start:
            continue
        if end and day > end:
            continue
        text = path.read_text(encoding="utf-8")
        try:
            _, sections = split_sections(text)
        except WorkflowError:
            continue
        _, must_rows = parse_table(sections.get("今日必须完成", ""))
        _, plan_rows = parse_table(sections.get("今日计划（非必须）", ""))
        _, adhoc_rows = parse_table(sections.get("临时新增", ""))
        _, completed_rows = parse_table(sections.get("实际完成", ""))
        _, incomplete_rows = parse_table(sections.get("未完成 & 原因", ""))

        id_to_project: dict[str, str] = {}
        title_to_project: dict[str, str] = {}
        for row in must_rows + plan_rows:
            task_id = row.get("ID", "")
            project = row.get("项目", "")
            title = row.get("标题", "")
            if task_id and project:
                id_to_project[task_id] = project
            if title and project:
                title_to_project[title] = project
        for row in adhoc_rows:
            title = row.get("标题", "")
            project = row.get("项目", "")
            if title and project:
                title_to_project[title] = project

        records.append(
            {
                "date": day,
                "path": path,
                "must": must_rows,
                "plan": plan_rows,
                "adhoc": adhoc_rows,
                "completed": completed_rows,
                "incomplete": incomplete_rows,
                "id_to_project": id_to_project,
                "title_to_project": title_to_project,
            }
        )
    return records


def week_bounds(anchor: dt.date) -> tuple[dt.date, dt.date]:
    start = anchor - dt.timedelta(days=anchor.weekday())
    end = start + dt.timedelta(days=6)
    return start, end


def month_bounds(anchor: dt.date) -> tuple[dt.date, dt.date]:
    start = anchor.replace(day=1)
    if anchor.month == 12:
        next_month = anchor.replace(year=anchor.year + 1, month=1, day=1)
    else:
        next_month = anchor.replace(month=anchor.month + 1, day=1)
    return start, next_month - dt.timedelta(days=1)


def quarter_bounds(anchor: dt.date) -> tuple[dt.date, dt.date]:
    quarter = ((anchor.month - 1) // 3) * 3 + 1
    start = dt.date(anchor.year, quarter, 1)
    if quarter == 10:
        end = dt.date(anchor.year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        end = dt.date(anchor.year, quarter + 3, 1) - dt.timedelta(days=1)
    return start, end


def halfyear_bounds(anchor: dt.date) -> tuple[dt.date, dt.date]:
    if anchor.month <= 6:
        return dt.date(anchor.year, 1, 1), dt.date(anchor.year, 6, 30)
    return dt.date(anchor.year, 7, 1), dt.date(anchor.year, 12, 31)


def relative_link(from_path: Path, to_path: Path, label: str) -> str:
    relative = os.path.relpath(to_path, start=from_path.parent)
    return f"[{label}]({relative.replace(os.sep, '/')})"


def project_page_content(root: Path, project: str, anchor: dt.date, tasks: list[dict[str, str]], records: list[dict[str, object]]) -> str:
    meta = PROJECTS[project]
    project_tasks = [task for task in tasks if task["project"] == project]
    done_tasks = [task for task in project_tasks if task["status"] == "done"]
    open_tasks = [task for task in project_tasks if task["status"] in OPEN_STATUSES]
    blocked_tasks = [task for task in project_tasks if task["status"] == "blocked"]
    overdue_tasks = [
        task
        for task in open_tasks
        if task["due_date"] and dt.date.fromisoformat(task["due_date"]) < anchor
    ]
    due_soon = sorted(
        [task for task in open_tasks if task["due_date"]],
        key=lambda task: dt.date.fromisoformat(task["due_date"]),
    )[:3]

    week_start, week_end = week_bounds(anchor)
    weekly_records = [record for record in records if week_start <= record["date"] <= week_end]

    completed_lines = []
    incomplete_lines = []
    source_refs: list[tuple[dt.date, Path]] = []
    for record in weekly_records:
        path = record["path"]
        day = record["date"]
        for row in record["completed"]:
            project_slug = record["id_to_project"].get(row.get("ID", "")) or record["title_to_project"].get(row.get("标题", ""))
            if project_slug == project:
                completed_lines.append(
                    f"- {day.isoformat()}: 完成 {row.get('标题', '')}。{row.get('完成情况', '').strip()}"
                )
                source_refs.append((day, path))
        for row in record["incomplete"]:
            project_slug = record["id_to_project"].get(row.get("ID", "")) or record["title_to_project"].get(row.get("标题", ""))
            if project_slug == project:
                reason = row.get("原因", "").strip()
                next_plan = row.get("后续计划", "").strip()
                incomplete_lines.append(
                    f"- {day.isoformat()}: {row.get('标题', '')} 未完成。原因：{reason or '未填写'}；后续：{next_plan or '未填写'}"
                )
                source_refs.append((day, path))

    unique_refs = []
    seen = set()
    for day, path in sorted(source_refs, key=lambda item: item[0]):
        key = (day, path)
        if key in seen:
            continue
        seen.add(key)
        unique_refs.append(f"- {relative_link(root / 'projects' / meta['filename'], path, day.isoformat())}")

    current_summary = [
        f"- 关注范围：{meta['focus']}",
        f"- 当前共有 {len(project_tasks)} 项任务，其中进行中 {sum(task['status'] == 'doing' for task in project_tasks)} 项，阻塞 {len(blocked_tasks)} 项，已完成 {len(done_tasks)} 项。",
    ]
    if overdue_tasks:
        current_summary.append(
            "- 已逾期任务："
            + "；".join(f"{task['title']}({task['due_date']})" for task in overdue_tasks[:3])
        )
    elif due_soon:
        current_summary.append(
            "- 近期交付："
            + "；".join(f"{task['title']}({task['due_date']})" for task in due_soon)
        )
    else:
        current_summary.append("- 当前没有填写 DDL 的近期交付项。")

    milestone_lines = []
    for task in sorted(
        [task for task in project_tasks if task["deliverable"]],
        key=lambda item: (
            dt.date.fromisoformat(item["due_date"]) if item["due_date"] else dt.date.max,
            PRIORITY_ORDER[item["priority"]],
            item["id"],
        ),
    )[:5]:
        ddl = task["due_date"] or "未填写"
        milestone_lines.append(f"- {task['deliverable']}：{task['title']}（{task['status']}，DDL {ddl}）")
    if not milestone_lines:
        milestone_lines = ["- 暂无结构化交付物。"]

    blocked_lines = [f"- {task['title']}（备注：{task['notes'] or '未填写'}）" for task in blocked_tasks]
    if not blocked_lines and incomplete_lines:
        blocked_lines = incomplete_lines
    if not blocked_lines:
        blocked_lines = ["- 当前无显式阻塞。"]

    progress_lines = completed_lines or ["- 本周暂无归档完成记录。"]

    lines = [
        f"# {meta['name']} ({project})",
        "",
        "## 当前状态摘要",
        "",
        *current_summary,
        "",
        "## 本周进展摘要",
        "",
        *progress_lines,
        "",
        "## 当前阻塞与风险",
        "",
        *blocked_lines,
        "",
        "## 近期里程碑 / 交付物",
        "",
        *milestone_lines,
        "",
        "## 源记录引用",
        "",
        *(unique_refs or ["- 本周暂无可引用的 daily 记录。"]),
        "",
        "> 此页由 `scripts/todo_workflow.py` 根据 `data/tasks.csv` 与 `daily/` 自动生成。",
        "",
    ]
    return "\n".join(lines)


def generate_project_pages(root: Path, anchor: dt.date) -> None:
    tasks = load_tasks(root)
    records = collect_daily_records(root)
    for slug, meta in PROJECTS.items():
        content = project_page_content(root, slug, anchor, tasks, records)
        write_text(root / "projects" / meta["filename"], content)


def aggregate_period(root: Path, start: dt.date, end: dt.date) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    tasks = load_tasks(root)
    records = collect_daily_records(root, start, end)
    return tasks, records


def summary_links(lines: list[str]) -> list[str]:
    return lines or ["- 暂无记录。"]


def project_heading(slug: str) -> str:
    return f"### {PROJECTS[slug]['name']} ({slug})"


def build_weekly_summary(root: Path, anchor: dt.date) -> str:
    start, end = week_bounds(anchor)
    tasks, records = aggregate_period(root, start, end)
    by_project_completed: dict[str, list[str]] = defaultdict(list)
    by_project_incomplete: dict[str, list[str]] = defaultdict(list)
    by_project_refs: dict[str, list[str]] = defaultdict(list)

    for record in records:
        day = record["date"]
        path = record["path"]
        for row in record["completed"]:
            project = record["id_to_project"].get(row.get("ID", "")) or record["title_to_project"].get(row.get("标题", ""))
            if not project:
                continue
            link = relative_link(weekly_summary_path(root, anchor), path, day.isoformat())
            by_project_completed[project].append(
                f"- 完成 {row.get('标题', '')}：{row.get('完成情况', '').strip() or '未填写完成说明'}。来源：{link}"
            )
        for row in record["incomplete"]:
            project = record["id_to_project"].get(row.get("ID", "")) or record["title_to_project"].get(row.get("标题", ""))
            if not project:
                continue
            link = relative_link(weekly_summary_path(root, anchor), path, day.isoformat())
            by_project_incomplete[project].append(
                f"- {row.get('标题', '')} 未完成。原因：{row.get('原因', '').strip() or '未填写'}；后续：{row.get('后续计划', '').strip() or '未填写'}。来源：{link}"
            )
        touched_projects = {
            row.get("项目", "")
            for row in record["must"] + record["plan"]
            if row.get("项目", "")
        }
        for project in touched_projects:
            link = relative_link(weekly_summary_path(root, anchor), path, day.isoformat())
            by_project_refs[project].append(link)

    by_project_active: dict[str, list[str]] = defaultdict(list)
    by_project_blocked: dict[str, list[str]] = defaultdict(list)
    by_project_overdue: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        if task["status"] == "doing":
            refs = by_project_refs.get(task["project"])
            source = refs[-1] if refs else "`data/tasks.csv`"
            by_project_active[task["project"]].append(
                f"- {task['title']}（状态 doing，DDL {task['due_date'] or '未填写'}）。来源：{source}"
            )
        if task["status"] == "blocked":
            refs = by_project_refs.get(task["project"])
            source = refs[-1] if refs else "`data/tasks.csv`"
            by_project_blocked[task["project"]].append(
                f"- {task['title']}（备注：{task['notes'] or '未填写'}）。来源：{source}"
            )
        if task["status"] in OPEN_STATUSES and task["due_date"] and dt.date.fromisoformat(task["due_date"]) < anchor:
            refs = by_project_refs.get(task["project"])
            source = refs[-1] if refs else "`data/tasks.csv`"
            by_project_overdue[task["project"]].append(
                f"- {task['title']} 已超过 DDL {task['due_date']}，当前状态 {task['status']}。来源：{source}"
            )

    lines = [
        f"# {anchor.isocalendar().year}-W{anchor.isocalendar().week:02d} 周报",
        "",
        f"- 周期：{start.isoformat()} 至 {end.isoformat()}",
        "",
        "## 本周完成",
        "",
    ]
    for slug in [key for key in PROJECTS if key != "MISC"]:
        lines.append(project_heading(slug))
        lines.append("")
        lines.extend(summary_links(by_project_completed.get(slug, [])))
        lines.append("")

    lines.extend(["## 进行中", ""])
    for slug in [key for key in PROJECTS if key != "MISC"]:
        lines.append(project_heading(slug))
        lines.append("")
        lines.extend(summary_links(by_project_active.get(slug, [])))
        lines.append("")

    lines.extend(["## 阻塞 / 风险", ""])
    for slug in [key for key in PROJECTS if key != "MISC"]:
        lines.append(project_heading(slug))
        lines.append("")
        lines.extend(summary_links((by_project_blocked.get(slug, []) + by_project_incomplete.get(slug, []))))
        lines.append("")

    lines.extend(["## 延期 / 未完成", ""])
    for slug in [key for key in PROJECTS if key != "MISC"]:
        lines.append(project_heading(slug))
        lines.append("")
        lines.extend(summary_links(by_project_overdue.get(slug, [])))
        lines.append("")

    lines.extend(["## 杂项（MISC）", ""])
    misc_lines = (
        by_project_completed.get("MISC", [])
        + by_project_active.get("MISC", [])
        + by_project_blocked.get("MISC", [])
        + by_project_incomplete.get("MISC", [])
        + by_project_overdue.get("MISC", [])
    )
    lines.extend(summary_links(misc_lines))
    lines.append("")
    return "\n".join(lines)


def build_monthly_summary(root: Path, anchor: dt.date) -> str:
    start, end = month_bounds(anchor)
    tasks, records = aggregate_period(root, start, end)
    completed = []
    issues = []
    for record in records:
        day = record["date"]
        path = record["path"]
        for row in record["completed"]:
            project = record["id_to_project"].get(row.get("ID", "")) or record["title_to_project"].get(row.get("标题", ""))
            if not project:
                continue
            link = relative_link(monthly_summary_path(root, anchor), path, day.isoformat())
            completed.append(f"- {PROJECTS[project]['name']}：{row.get('标题', '')}。来源：{link}")
        for row in record["incomplete"]:
            project = record["id_to_project"].get(row.get("ID", "")) or record["title_to_project"].get(row.get("标题", ""))
            if not project:
                continue
            link = relative_link(monthly_summary_path(root, anchor), path, day.isoformat())
            issues.append(f"- {PROJECTS[project]['name']}：{row.get('标题', '')}。原因：{row.get('原因', '') or '未填写'}。来源：{link}")

    next_focus = []
    for task in sort_open_tasks([task for task in tasks if task["status"] in OPEN_STATUSES])[:8]:
        next_focus.append(
            f"- {PROJECTS[task['project']]['name']}：{task['title']}（{task['priority']}，DDL {task['due_date'] or '未填写'}）"
        )

    lines = [
        f"# {anchor.year}-{anchor.month:02d} 月报",
        "",
        f"- 周期：{start.isoformat()} 至 {end.isoformat()}",
        "",
        "## 里程碑达成",
        "",
        *summary_links(completed),
        "",
        "## 偏差分析",
        "",
        *summary_links(issues),
        "",
        "## 下月关注点",
        "",
        *summary_links(next_focus),
        "",
    ]
    return "\n".join(lines)


def build_range_summary(root: Path, anchor: dt.date, bounds_fn, title: str, output_path: Path) -> str:
    start, end = bounds_fn(anchor)
    tasks, records = aggregate_period(root, start, end)
    completed = 0
    unresolved = 0
    source_refs = []
    for record in records:
        completed += len(record["completed"])
        unresolved += len(record["incomplete"])
        source_refs.append(relative_link(output_path, record["path"], record["date"].isoformat()))

    open_focus = [
        f"- {PROJECTS[task['project']]['name']}：{task['title']}（{task['status']}，DDL {task['due_date'] or '未填写'}）"
        for task in sort_open_tasks([task for task in tasks if task["status"] in OPEN_STATUSES])[:10]
    ]
    lines = [
        f"# {title}",
        "",
        f"- 周期：{start.isoformat()} 至 {end.isoformat()}",
        "",
        "## 阶段达成",
        "",
        f"- 归档完成记录 {completed} 条。",
        "",
        "## 主要风险",
        "",
        f"- 未完成 / 风险记录 {unresolved} 条。",
        "",
        "## 下阶段关注点",
        "",
        *summary_links(open_focus),
        "",
        "## 源记录引用",
        "",
        *summary_links(sorted(set(source_refs))),
        "",
    ]
    return "\n".join(lines)


def generate_today_command(root: Path, anchor: dt.date) -> None:
    write_text(today_path(root), render_today(root, anchor))


def close_day_command(root: Path, anchor: dt.date | None) -> None:
    archived_day, _ = sync_today(root)
    if anchor and anchor != archived_day:
        raise WorkflowError(f"today.md date {archived_day} does not match requested date {anchor}")
    generate_project_pages(root, archived_day)


def write_summary(path: Path, content: str) -> None:
    write_text(path, content)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    command = args.command

    if command == "generate-today":
        generate_today_command(root, today_date(args.date))
        return 0
    if command == "close-day":
        close_day_command(root, today_date(args.date) if args.date else None)
        return 0
    if command == "generate-projects":
        generate_project_pages(root, dt.date.today())
        return 0
    if command == "generate-weekly":
        anchor = today_date(args.date)
        write_summary(weekly_summary_path(root, anchor), build_weekly_summary(root, anchor))
        return 0
    if command == "generate-monthly":
        anchor = today_date(args.date)
        write_summary(monthly_summary_path(root, anchor), build_monthly_summary(root, anchor))
        return 0
    if command == "generate-quarterly":
        anchor = today_date(args.date)
        quarter = ((anchor.month - 1) // 3) + 1
        write_summary(
            quarter_summary_path(root, anchor),
            build_range_summary(
                root,
                anchor,
                quarter_bounds,
                f"{anchor.year} Q{quarter} 季报",
                quarter_summary_path(root, anchor),
            ),
        )
        return 0
    if command == "generate-halfyear":
        anchor = today_date(args.date)
        half = 1 if anchor.month <= 6 else 2
        write_summary(
            halfyear_summary_path(root, anchor),
            build_range_summary(
                root,
                anchor,
                halfyear_bounds,
                f"{anchor.year} H{half} 半年报",
                halfyear_summary_path(root, anchor),
            ),
        )
        return 0
    raise WorkflowError(f"Unknown command: {command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowError as exc:
        raise SystemExit(f"error: {exc}")
