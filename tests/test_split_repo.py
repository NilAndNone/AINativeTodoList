from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPLIT_SCRIPT = REPO_ROOT / "scripts" / "split_repo.py"
WORKFLOW_SCRIPT = REPO_ROOT / "scripts" / "todo_workflow.py"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


TASKS_CSV = "\n".join(
    [
        "id,title,project,priority,created_date,due_date,deliverable,status,notes",
        "UTC-20260304-01,推进性能优化,UTC,P0,2026-03-04,2026-03-06,分析报告,doing,当前在推进",
        "AGE-20260304-01,输出阶段性计划文档,AGE,P1,2026-03-04,,阶段性计划文档,todo,待开始",
    ]
) + "\n"


class SplitRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.source = self.root / "source_repo"
        self.target = self.root / "target_repo"
        write_file(self.source / "data" / "tasks.csv", TASKS_CSV)
        write_file(self.source / "today.md", "# 已归档\n")
        write_file(self.source / "reports" / "templates" / "weekly-template.md", "weekly template\n")
        write_file(self.source / "projects" / "unit-test-client.md", "# UTC\n")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_split(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SPLIT_SCRIPT), "--source", str(self.source), "--target", str(self.target), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_split_repo_copies_targets_and_writes_config(self) -> None:
        result = self.run_split()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.target / "data" / "tasks.csv").exists())
        self.assertTrue((self.target / "today.md").exists())
        self.assertTrue((self.target / "reports" / "templates" / "weekly-template.md").exists())
        todo_config = (self.target / "todo.config.toml").read_text(encoding="utf-8")
        self.assertIn('task_store = "data/tasks.csv"', todo_config)
        self.assertIn("[projects.UTC]", todo_config)

    def test_split_target_can_be_driven_by_existing_cli_with_root(self) -> None:
        split_result = self.run_split()
        self.assertEqual(split_result.returncode, 0, split_result.stderr)

        result = subprocess.run(
            [
                sys.executable,
                str(WORKFLOW_SCRIPT),
                "--root",
                str(self.target),
                "generate-today",
                "--date",
                "2026-03-04",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        today = (self.target / "today.md").read_text(encoding="utf-8")
        self.assertIn("## 今日必须完成", today)
        self.assertIn("UTC-20260304-01", today)


if __name__ == "__main__":
    unittest.main()
