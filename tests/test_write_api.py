from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from ainative_todo_service.write_api import WritePlanner


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


DATA_CONFIG = """
schema_version = 1

[paths]
task_store = "data/tasks.csv"
today_file = "today.md"
daily_dir = "daily"
reports_dir = "reports"
projects_dir = "projects"

[storage]
format = "csv"

[projects.UTC]
name = "单测客户端"
file = "unit-test-client.md"
focus = "客户端工程实现、稳定性、性能、监控与离线流程建设。"

[projects.AGE]
name = "单测评测"
file = "agent-evaluation.md"
focus = "单元测试代码生成 agent 的评测框架与阶段性输出。"

[projects.MISC]
name = "杂项"
file = "misc.md"
focus = "临时支持、会议、沟通和跨项目事项。"
""".strip() + "\n"


TASKS_CSV = "\n".join(
    [
        "id,title,project,priority,created_date,due_date,deliverable,status,notes",
        "UTC-20260309-01,推进性能优化,UTC,P0,2026-03-09,2026-03-09,分析报告,doing,等待回归验证",
        "UTC-20260309-02,推进性能优化二期,UTC,P1,2026-03-09,2026-03-11,回归结论,todo,待开始",
        "AGE-20260309-01,输出阶段性计划,AGE,P2,2026-03-09,,阶段性计划文档,todo,待开始",
    ]
) + "\n"


TODAY_MARKDOWN = "\n".join(
    [
        "# 2026-03-09 周一",
        "",
        "## 今日必须完成",
        "",
        "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "| UTC-20260309-01 | 推进性能优化 | UTC | P0 | 2026-03-09 | 2026-03-09 | 分析报告 | doing | 等待回归验证 |",
        "",
        "## 今日计划（非必须）",
        "",
        "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "| AGE-20260309-01 | 输出阶段性计划 | AGE | P2 | 2026-03-09 |  | 阶段性计划文档 | todo | 待开始 |",
        "",
        "## 临时新增",
        "",
        "| 标题 | 项目 | P | DDL | 产出 | 状态 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        "|  |  |  |  |  |  |  |",
        "",
        "## 实际完成",
        "",
        "| ID | 标题 | 完成情况 |",
        "| --- | --- | --- |",
        "|  |  |  |",
        "",
        "## 未完成 & 原因",
        "",
        "| ID | 标题 | 原因 | 后续计划 |",
        "| --- | --- | --- | --- |",
        "|  |  |  |  |",
        "",
        "## 备注",
        "",
        "写入动作层测试。",
        "",
    ]
)


class WriteApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.data_repo = self.root / "data_repo"
        self.data_repo.mkdir()
        write_file(self.data_repo / "todo.config.toml", DATA_CONFIG)
        write_file(self.data_repo / "data" / "tasks.csv", TASKS_CSV)
        write_file(self.data_repo / "today.md", TODAY_MARKDOWN)
        self.runtime_config_path = self.root / "config.toml"
        write_file(
            self.runtime_config_path,
            f'profile = "local"\ndata_repo = "{self.data_repo}"\n',
        )
        self.planner = WritePlanner(config_path=self.runtime_config_path, code_repo=REPO_ROOT)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_plan_add_task_requests_missing_fields(self) -> None:
        payload = self.planner.plan_write(action="add_task", args={"title": "整理周会纪要", "project": "MISC"})
        self.assertEqual(payload["status"], "needs_input")
        missing_fields = {item["field"] for item in payload["missing_fields"]}
        self.assertEqual(missing_fields, {"priority", "deliverable", "status"})

    def test_plan_update_task_returns_ambiguous_candidates(self) -> None:
        payload = self.planner.plan_write(
            action="update_task",
            args={
                "task_selector": {"query": "性能优化"},
                "patch": {"status": "blocked", "notes": "等待接口"},
            },
        )
        self.assertEqual(payload["status"], "ambiguous")
        self.assertEqual(len(payload["candidates"]), 2)

    def test_plan_and_apply_update_task_syncs_today_and_csv(self) -> None:
        before_today = (self.data_repo / "today.md").read_text(encoding="utf-8")
        payload = self.planner.plan_write(
            action="update_task",
            args={
                "task_selector": {"id": "UTC-20260309-01"},
                "patch": {
                    "title": "推进性能优化 v2",
                    "project": "AGE",
                    "priority": "P1",
                    "due_date": "2026-03-12",
                    "deliverable": "阶段二分析报告",
                    "status": "blocked",
                    "notes": "等待依赖方接口",
                },
            },
        )

        self.assertEqual(payload["status"], "ready_for_confirm")
        self.assertEqual(set(payload["files_changed"]), {"data/tasks.csv", "today.md"})
        self.assertIn("推进性能优化 v2", payload["diffs"][0]["unified_diff"] + payload["diffs"][1]["unified_diff"])
        self.assertEqual((self.data_repo / "today.md").read_text(encoding="utf-8"), before_today)

        apply_payload = self.planner.apply(operation_id=payload["operation_id"])
        self.assertTrue(apply_payload["ok"])
        self.assertEqual(apply_payload["action"], "update_task")

        with (self.data_repo / "data" / "tasks.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        task = next(row for row in rows if row["id"] == "UTC-20260309-01")
        self.assertEqual(task["title"], "推进性能优化 v2")
        self.assertEqual(task["project"], "AGE")
        self.assertEqual(task["priority"], "P1")
        self.assertEqual(task["due_date"], "2026-03-12")
        self.assertEqual(task["deliverable"], "阶段二分析报告")
        self.assertEqual(task["status"], "blocked")
        self.assertEqual(task["notes"], "等待依赖方接口")

        today_text = (self.data_repo / "today.md").read_text(encoding="utf-8")
        self.assertIn("推进性能优化 v2", today_text)
        self.assertIn("| UTC-20260309-01 | 推进性能优化 v2 | AGE | P1 | 2026-03-09 | 2026-03-12 | 阶段二分析报告 | blocked | 等待依赖方接口 |", today_text)

    def test_plan_and_apply_add_task_generates_stable_id_and_updates_today(self) -> None:
        payload = self.planner.plan_write(
            action="add_task",
            args={
                "title": "整理周会纪要",
                "project": "MISC",
                "priority": "P2",
                "deliverable": "会议纪要",
                "status": "todo",
                "due_date": "2026-03-10",
                "notes": "新增临时任务",
                "created_date": "2026-03-09",
            },
        )

        self.assertEqual(payload["status"], "ready_for_confirm")
        self.assertEqual(set(payload["files_changed"]), {"data/tasks.csv", "today.md"})
        diff_text = "\n".join(item["unified_diff"] for item in payload["diffs"])
        self.assertIn("MISC-20260309-01", diff_text)
        self.assertNotIn("整理周会纪要", (self.data_repo / "today.md").read_text(encoding="utf-8"))

        apply_payload = self.planner.apply(operation_id=payload["operation_id"])
        self.assertTrue(apply_payload["ok"])

        with (self.data_repo / "data" / "tasks.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        task = next(row for row in rows if row["id"] == "MISC-20260309-01")
        self.assertEqual(task["title"], "整理周会纪要")
        self.assertEqual(task["deliverable"], "会议纪要")

        today_text = (self.data_repo / "today.md").read_text(encoding="utf-8")
        self.assertIn("| MISC-20260309-01 | 整理周会纪要 | MISC | P2 | 2026-03-09 | 2026-03-10 | 会议纪要 | todo | 新增临时任务 |", today_text)

    def test_apply_rejects_unknown_operation_id(self) -> None:
        payload = self.planner.apply(operation_id="op_missing")
        self.assertFalse(payload["ok"])
        self.assertIn("Unknown operation_id", payload["error"])

    def test_required_actions_are_supported(self) -> None:
        responses = {
            "start_day": self.planner.plan_write(action="start_day", args={}),
            "update_task": self.planner.plan_write(action="update_task", args={}),
            "add_task": self.planner.plan_write(action="add_task", args={}),
            "mark_done": self.planner.plan_write(action="mark_done", args={}),
            "mark_blocked": self.planner.plan_write(action="mark_blocked", args={}),
            "unblock_task": self.planner.plan_write(action="unblock_task", args={}),
            "change_priority": self.planner.plan_write(action="change_priority", args={}),
            "change_due_date": self.planner.plan_write(action="change_due_date", args={}),
            "cancel_task": self.planner.plan_write(action="cancel_task", args={}),
            "close_day": self.planner.plan_write(action="close_day", args={"date": "2026-03-09"}),
            "generate_report": self.planner.plan_write(action="generate_report", args={"report_type": "weekly", "date": "2026-03-09"}),
            "rebuild_projects": self.planner.plan_write(action="rebuild_projects", args={}),
        }
        for action, payload in responses.items():
            self.assertNotEqual(payload["status"], "error", action)


if __name__ == "__main__":
    unittest.main()
