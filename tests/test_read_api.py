from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ainative_todo_service.read_api import (
    build_doctor_payload,
    build_overview_payload,
    build_today_markdown_payload,
    search_tasks_payload,
)


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

[projects.MISC]
name = "杂项"
file = "misc.md"
focus = "临时支持、会议、沟通和跨项目事项。"
""".strip() + "\n"


TASKS_CSV = "\n".join(
    [
        "id,title,project,priority,created_date,due_date,deliverable,status,notes",
        "UTC-20260304-01,推进性能优化,UTC,P0,2026-03-04,2026-03-09,分析报告,doing,等待回归验证",
        "UTC-20260305-01,补充压测结论,UTC,P1,2026-03-05,2026-03-08,压测纪要,blocked,等依赖方接口",
        "MISC-20260305-01,整理周会纪要,MISC,P2,2026-03-05,,会议纪要,todo,待整理",
        "MISC-20260306-01,处理临时支持,MISC,P3,2026-03-06,,沟通记录,done,已完成",
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
        "| UTC-20260304-01 | 推进性能优化 | UTC | P0 | 2026-03-04 | 2026-03-09 | 分析报告 | doing | 等待回归验证 |",
        "",
        "## 今日计划（非必须）",
        "",
        "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "| MISC-20260305-01 | 整理周会纪要 | MISC | P2 | 2026-03-05 |  | 会议纪要 | todo | 待整理 |",
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
        "阶段 3 读取测试。",
        "",
    ]
)


class ReadApiTests(unittest.TestCase):
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

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_build_doctor_payload_exposes_read_capabilities(self) -> None:
        payload = build_doctor_payload(config_path=self.runtime_config_path, code_repo=REPO_ROOT)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["storage_format"], "csv")
        self.assertIn("todo_get_overview", payload["supported_read_tools"])

    def test_build_overview_payload_summarizes_today_and_open_work(self) -> None:
        payload = build_overview_payload(
            date="2026-03-09",
            config_path=self.runtime_config_path,
            code_repo=REPO_ROOT,
        )
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["today_exists"])
        self.assertFalse(payload["today_archived"])
        self.assertEqual(payload["today_heading_date"], "2026-03-09")
        self.assertEqual(payload["must_do_count"], 2)
        self.assertEqual([task["id"] for task in payload["blocked"]], ["UTC-20260305-01"])
        self.assertEqual([task["id"] for task in payload["overdue"]], ["UTC-20260305-01"])
        self.assertEqual([task["id"] for task in payload["doing"]], ["UTC-20260304-01"])

    def test_build_today_markdown_payload_returns_raw_markdown(self) -> None:
        payload = build_today_markdown_payload(config_path=self.runtime_config_path, code_repo=REPO_ROOT)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["today_exists"])
        self.assertIn("## 今日必须完成", payload["markdown"])

    def test_search_tasks_payload_filters_by_query_and_status(self) -> None:
        payload = search_tasks_payload(
            query="性能优化",
            status=["doing", "blocked"],
            limit=5,
            config_path=self.runtime_config_path,
            code_repo=REPO_ROOT,
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["total_matches"], 1)
        self.assertEqual(payload["matches"][0]["id"], "UTC-20260304-01")


if __name__ == "__main__":
    unittest.main()
