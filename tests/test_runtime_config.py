from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ainative_todo_service.config import load_data_repo_config, load_runtime_config
from ainative_todo_service.doctor import build_report


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

[git]
auto_commit_on_close_day = true
auto_push_on_close_day = false
commit_message = "chore(todo): close day {date}"

[projects.UTC]
name = "单测客户端"
file = "unit-test-client.md"
focus = "客户端工程实现、稳定性、性能、监控与离线流程建设。"
""".strip() + "\n"


class RuntimeConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.data_repo = self.root / "data_repo"
        self.data_repo.mkdir()
        write_file(self.data_repo / "todo.config.toml", DATA_CONFIG)
        write_file(self.data_repo / "data" / "tasks.csv", "id,title,project,priority,created_date,due_date,deliverable,status,notes\n")
        self.runtime_config_path = self.root / "config.toml"
        write_file(
            self.runtime_config_path,
            f'profile = "local"\ndata_repo = "{self.data_repo}"\n',
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_load_runtime_and_data_repo_config(self) -> None:
        runtime_config = load_runtime_config(self.runtime_config_path, code_repo=REPO_ROOT)
        self.assertEqual(runtime_config.code_repo, REPO_ROOT)
        self.assertEqual(runtime_config.data_repo, self.data_repo.resolve())
        self.assertEqual(runtime_config.profile, "local")

        data_config = load_data_repo_config(runtime_config.data_repo)
        self.assertEqual(data_config.schema_version, 1)
        self.assertEqual(data_config.resolve_path("task_store"), (self.data_repo / "data" / "tasks.csv").resolve())
        self.assertEqual(sorted(data_config.projects), ["UTC"])
        self.assertTrue(data_config.git.auto_commit_on_close_day)
        self.assertFalse(data_config.git.auto_push_on_close_day)

    def test_build_report_and_module_invocation(self) -> None:
        report = build_report(config_path=self.runtime_config_path, code_repo=REPO_ROOT)
        self.assertTrue(report["ok"])
        self.assertEqual(report["data_repo"], str(self.data_repo.resolve()))
        self.assertEqual(report["resolved_paths"]["today_file"], str((self.data_repo / "today.md").resolve()))
        self.assertTrue(report["git"]["auto_commit_on_close_day"])
        self.assertFalse(report["git"]["auto_push_on_close_day"])

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ainative_todo_service.doctor",
                "--config",
                str(self.runtime_config_path),
                "--code-repo",
                str(REPO_ROOT),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["code_repo"], str(REPO_ROOT))
        self.assertEqual(payload["projects"], ["UTC"])


if __name__ == "__main__":
    unittest.main()
