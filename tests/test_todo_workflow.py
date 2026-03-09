from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "todo_workflow.py"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TodoWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        write_file(
            self.root / "data" / "tasks.csv",
            "\n".join(
                [
                    "id,title,project,priority,created_date,due_date,deliverable,status,notes",
                    "UTC-20260304-01,推进性能优化,UTC,P0,2026-03-04,2026-03-06,分析报告,doing,当前在推进",
                    "AGE-20260304-01,输出阶段性计划文档,AGE,P1,2026-03-04,,阶段性计划文档,todo,待开始",
                    "MISC-20260304-01,处理临时支持,MISC,P2,2026-03-04,,沟通记录,todo,记录杂项",
                ]
            )
            + "\n",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_generate_today_splits_open_tasks(self) -> None:
        result = self.run_cli("generate-today", "--date", "2026-03-04")
        self.assertEqual(result.returncode, 0, result.stderr)
        today = (self.root / "today.md").read_text(encoding="utf-8")
        self.assertIn("## 今日必须完成", today)
        self.assertIn("UTC-20260304-01", today)
        self.assertIn("## 今日计划（非必须）", today)
        self.assertIn("AGE-20260304-01", today)
        self.assertIn("MISC-20260304-01", today)

    def test_close_day_updates_csv_and_archives(self) -> None:
        write_file(
            self.root / "today.md",
            "\n".join(
                [
                    "# 2026-03-04 周三",
                    "",
                    "## 今日必须完成",
                    "",
                    "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| UTC-20260304-01 | 推进性能优化 | UTC | P0 | 2026-03-04 | 2026-03-06 | 分析报告 | doing | 当天补齐性能回归 |",
                    "",
                    "## 今日计划（非必须）",
                    "",
                    "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| AGE-20260304-01 | 输出阶段性计划文档 | AGE | P1 | 2026-03-04 |  | 阶段性计划文档 | todo | 待开始 |",
                    "",
                    "## 临时新增",
                    "",
                    "| 标题 | 项目 | P | DDL | 产出 | 状态 | 备注 |",
                    "| --- | --- | --- | --- | --- | --- | --- |",
                    "| 处理临时评审反馈 | MISC | P1 | 2026-03-04 | 评审纪要 | done | 当天插入 |",
                    "",
                    "## 实际完成",
                    "",
                    "| ID | 标题 | 完成情况 |",
                    "| --- | --- | --- |",
                    "| UTC-20260304-01 | 推进性能优化 | 完成主要回归验证 |",
                    "|  | 处理临时评审反馈 | 评审反馈已同步 |",
                    "",
                    "## 未完成 & 原因",
                    "",
                    "| ID | 标题 | 原因 | 后续计划 |",
                    "| --- | --- | --- | --- |",
                    "| AGE-20260304-01 | 输出阶段性计划文档 | 还在补背景 | 明天继续 |",
                    "",
                    "## 备注",
                    "",
                    "今天主要收敛了性能相关事项。",
                    "",
                ],
            ),
        )
        result = self.run_cli("close-day", "--date", "2026-03-04")
        self.assertEqual(result.returncode, 0, result.stderr)

        with (self.root / "data" / "tasks.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        utc = next(row for row in rows if row["id"] == "UTC-20260304-01")
        misc = next(row for row in rows if row["title"] == "处理临时评审反馈")
        self.assertEqual(utc["status"], "done")
        self.assertEqual(utc["notes"], "当天补齐性能回归")
        self.assertEqual(misc["status"], "done")
        self.assertEqual(misc["project"], "MISC")

        archive = self.root / "daily" / "2026-03" / "W10" / "2026-03-04.md"
        self.assertTrue(archive.exists())
        self.assertIn("已归档到", (self.root / "today.md").read_text(encoding="utf-8"))
        self.assertTrue((self.root / "projects" / "unit-test-client.md").exists())

    def test_generate_weekly_contains_source_links(self) -> None:
        archive = self.root / "daily" / "2026-03" / "W10" / "2026-03-04.md"
        write_file(
            archive,
            "\n".join(
                [
                    "# 2026-03-04 周三",
                    "",
                    "## 今日必须完成",
                    "",
                    "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| UTC-20260304-01 | 推进性能优化 | UTC | P0 | 2026-03-04 | 2026-03-06 | 分析报告 | done | 当前在推进 |",
                    "",
                    "## 今日计划（非必须）",
                    "",
                    "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| AGE-20260304-01 | 输出阶段性计划文档 | AGE | P1 | 2026-03-04 |  | 阶段性计划文档 | doing | 待开始 |",
                    "| MISC-20260304-01 | 处理临时支持 | MISC | P2 | 2026-03-04 |  | 沟通记录 | todo | 记录杂项 |",
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
                    "| UTC-20260304-01 | 推进性能优化 | 完成主要回归验证 |",
                    "",
                    "## 未完成 & 原因",
                    "",
                    "| ID | 标题 | 原因 | 后续计划 |",
                    "| --- | --- | --- | --- |",
                    "| AGE-20260304-01 | 输出阶段性计划文档 | 还在补背景 | 明天继续 |",
                    "",
                    "## 备注",
                    "",
                    "周中推进。",
                    "",
                ]
            ),
        )
        result = self.run_cli("generate-weekly", "--date", "2026-03-04")
        self.assertEqual(result.returncode, 0, result.stderr)
        weekly = (self.root / "daily" / "2026-03" / "W10" / "weekly-summary.md").read_text(encoding="utf-8")
        self.assertIn("来源：[2026-03-04](2026-03-04.md)", weekly)
        self.assertIn("## 杂项（MISC）", weekly)
        self.assertNotIn("已超过 DDL 2026-03-06", weekly)

    def test_close_day_syncs_editable_existing_task_fields(self) -> None:
        write_file(
            self.root / "today.md",
            "\n".join(
                [
                    "# 2026-03-04 周三",
                    "",
                    "## 今日必须完成",
                    "",
                    "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| UTC-20260304-01 | 推进性能优化 v2 | AGE | P1 | 2026-03-04 | 2026-03-08 | 阶段二分析报告 | blocked | 等依赖接口 |",
                    "",
                    "## 今日计划（非必须）",
                    "",
                    "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| AGE-20260304-01 | 输出阶段性计划文档 | AGE | P1 | 2026-03-04 |  | 阶段性计划文档 | todo | 待开始 |",
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
                    "更新已有任务字段。",
                    "",
                ],
            ),
        )

        result = self.run_cli("close-day", "--date", "2026-03-04")
        self.assertEqual(result.returncode, 0, result.stderr)

        with (self.root / "data" / "tasks.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        task = next(row for row in rows if row["id"] == "UTC-20260304-01")
        self.assertEqual(task["title"], "推进性能优化 v2")
        self.assertEqual(task["project"], "AGE")
        self.assertEqual(task["priority"], "P1")
        self.assertEqual(task["due_date"], "2026-03-08")
        self.assertEqual(task["deliverable"], "阶段二分析报告")
        self.assertEqual(task["status"], "blocked")
        self.assertEqual(task["notes"], "等依赖接口")


if __name__ == "__main__":
    unittest.main()
