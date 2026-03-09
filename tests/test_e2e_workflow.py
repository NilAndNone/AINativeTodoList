from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


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

[git]
auto_commit_on_close_day = true
auto_push_on_close_day = true
commit_message = "chore(todo): close day {date}"

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
        "AGE-20260309-01,输出阶段性计划,AGE,P2,2026-03-09,,阶段性计划文档,todo,待开始",
    ]
) + "\n"


FAKE_GIT_SCRIPT = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import os
    import sys
    from pathlib import Path

    log_path = Path(os.environ["FAKE_GIT_LOG"])
    fail_on = os.environ.get("FAKE_GIT_FAIL_ON", "")
    args = sys.argv[1:]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"cwd": os.getcwd(), "args": args}, ensure_ascii=False) + "\\n")

    if args[:2] == ["rev-parse", "--is-inside-work-tree"]:
        print("true")
        raise SystemExit(0)
    if args[:2] == ["diff", "--cached"] and "--quiet" in args:
        raise SystemExit(1)
    if args[:2] == ["rev-parse", "HEAD"]:
        print("abc123def456")
        raise SystemExit(0)
    if args and args[0] == fail_on:
        print(f"fatal: mock {fail_on} failure", file=sys.stderr)
        raise SystemExit(1)

    raise SystemExit(0)
    """
)


class EndToEndWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.data_repo = self.root / "data_repo"
        self.data_repo.mkdir()
        write_file(self.data_repo / "todo.config.toml", DATA_CONFIG)
        write_file(self.data_repo / "data" / "tasks.csv", TASKS_CSV)
        self.runtime_config_path = self.root / "config.toml"
        write_file(
            self.runtime_config_path,
            f'profile = "local"\ndata_repo = "{self.data_repo}"\n',
        )
        self.fake_git = self.root / "fake_git.py"
        write_file(self.fake_git, FAKE_GIT_SCRIPT)
        self.fake_git.chmod(0o755)
        self.git_log = self.root / "git.log"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _call_payload(self, result) -> dict[str, object]:
        self.assertFalse(result.isError)
        return result.structuredContent or json.loads(result.content[0].text)

    def test_mcp_e2e_flow_covers_start_update_add_report_close_and_git(self) -> None:
        async def scenario() -> None:
            server = StdioServerParameters(
                command=sys.executable,
                args=["-m", "ainative_todo_service.mcp_server"],
                cwd=REPO_ROOT,
                env={
                    **os.environ,
                    "AINATIVE_TODO_CONFIG": str(self.runtime_config_path),
                    "AINATIVE_TODO_GIT_BIN": str(self.fake_git),
                    "FAKE_GIT_LOG": str(self.git_log),
                },
            )
            async with stdio_client(server) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    start_plan = self._call_payload(
                        await session.call_tool(
                            "todo_plan_write",
                            {"action": "start_day", "args": {"date": "2026-03-09"}},
                        )
                    )
                    self.assertEqual(start_plan["status"], "ready_for_confirm")
                    start_apply = self._call_payload(
                        await session.call_tool("todo_apply", {"operation_id": start_plan["operation_id"]})
                    )
                    self.assertTrue(start_apply["ok"])
                    self.assertTrue((self.data_repo / "today.md").exists())

                    update_plan = self._call_payload(
                        await session.call_tool(
                            "todo_plan_write",
                            {
                                "action": "update_task",
                                "args": {
                                    "task_selector": {"id": "UTC-20260309-01"},
                                    "patch": {"status": "blocked", "notes": "等待接口联调"},
                                },
                            },
                        )
                    )
                    self.assertEqual(update_plan["status"], "ready_for_confirm")
                    update_apply = self._call_payload(
                        await session.call_tool("todo_apply", {"operation_id": update_plan["operation_id"]})
                    )
                    self.assertTrue(update_apply["ok"])

                    add_plan = self._call_payload(
                        await session.call_tool(
                            "todo_plan_write",
                            {
                                "action": "add_task",
                                "args": {
                                    "title": "整理周会纪要",
                                    "project": "MISC",
                                    "priority": "P1",
                                    "deliverable": "会议纪要",
                                    "status": "todo",
                                    "due_date": "2026-03-10",
                                    "notes": "下午同步",
                                    "created_date": "2026-03-09",
                                },
                            },
                        )
                    )
                    self.assertEqual(add_plan["status"], "ready_for_confirm")
                    add_apply = self._call_payload(
                        await session.call_tool("todo_apply", {"operation_id": add_plan["operation_id"]})
                    )
                    self.assertTrue(add_apply["ok"])

                    report_plan = self._call_payload(
                        await session.call_tool(
                            "todo_plan_write",
                            {
                                "action": "generate_report",
                                "args": {"report_type": "weekly", "date": "2026-03-09"},
                            },
                        )
                    )
                    self.assertEqual(report_plan["status"], "ready_for_confirm")
                    report_apply = self._call_payload(
                        await session.call_tool("todo_apply", {"operation_id": report_plan["operation_id"]})
                    )
                    self.assertTrue(report_apply["ok"])
                    self.assertTrue((self.data_repo / "daily" / "2026-03" / "W11" / "weekly-summary.md").exists())

                    close_plan = self._call_payload(
                        await session.call_tool(
                            "todo_plan_write",
                            {"action": "close_day", "args": {"date": "2026-03-09"}},
                        )
                    )
                    self.assertEqual(close_plan["status"], "ready_for_confirm")
                    self.assertIn("git commit + push", " ".join(close_plan["warnings"]))
                    close_apply = self._call_payload(
                        await session.call_tool("todo_apply", {"operation_id": close_plan["operation_id"]})
                    )
                    self.assertTrue(close_apply["ok"])
                    self.assertEqual(close_apply["action"], "close_day")
                    self.assertTrue(close_apply["git"]["ok"])
                    self.assertEqual(close_apply["git"]["commit_status"], "created")
                    self.assertEqual(close_apply["git"]["push_status"], "pushed")
                    self.assertEqual(close_apply["git"]["commit_hash"], "abc123def456")

        anyio.run(scenario)

        archive = self.data_repo / "daily" / "2026-03" / "W11" / "2026-03-09.md"
        self.assertTrue(archive.exists())
        self.assertIn("已归档到", (self.data_repo / "today.md").read_text(encoding="utf-8"))

        tasks_csv = (self.data_repo / "data" / "tasks.csv").read_text(encoding="utf-8")
        self.assertIn("UTC-20260309-01,推进性能优化,UTC,P0,2026-03-09,2026-03-09,分析报告,blocked,等待接口联调", tasks_csv)
        self.assertIn("MISC-20260309-01,整理周会纪要,MISC,P1,2026-03-09,2026-03-10,会议纪要,todo,下午同步", tasks_csv)

        log_entries = [json.loads(line) for line in self.git_log.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(log_entries), 5)
        self.assertTrue(all(Path(entry["cwd"]).resolve() == self.data_repo.resolve() for entry in log_entries))
        self.assertIn(["push"], [entry["args"] for entry in log_entries])


if __name__ == "__main__":
    unittest.main()
