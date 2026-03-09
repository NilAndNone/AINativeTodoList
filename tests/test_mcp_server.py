from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
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

[projects.UTC]
name = "单测客户端"
file = "unit-test-client.md"
focus = "客户端工程实现、稳定性、性能、监控与离线流程建设。"
""".strip() + "\n"


TASKS_CSV = "\n".join(
    [
        "id,title,project,priority,created_date,due_date,deliverable,status,notes",
        "UTC-20260304-01,推进性能优化,UTC,P0,2026-03-04,2026-03-09,分析报告,doing,等待回归验证",
        "UTC-20260305-01,补充压测结论,UTC,P1,2026-03-05,2026-03-08,压测纪要,blocked,等依赖方接口",
    ]
) + "\n"


class McpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.data_repo = self.root / "data_repo"
        self.data_repo.mkdir()
        write_file(self.data_repo / "todo.config.toml", DATA_CONFIG)
        write_file(self.data_repo / "data" / "tasks.csv", TASKS_CSV)
        write_file(self.data_repo / "today.md", "# 已归档\n")
        self.runtime_config_path = self.root / "config.toml"
        write_file(
            self.runtime_config_path,
            f'profile = "local"\ndata_repo = "{self.data_repo}"\n',
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_mcp_server_lists_and_calls_read_tools(self) -> None:
        async def scenario() -> None:
            server = StdioServerParameters(
                command=sys.executable,
                args=["-m", "ainative_todo_service.mcp_server"],
                cwd=REPO_ROOT,
                env={
                    **os.environ,
                    "AINATIVE_TODO_CONFIG": str(self.runtime_config_path),
                },
            )
            async with stdio_client(server) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    tool_names = {tool.name for tool in tools_result.tools}
                    self.assertEqual(
                        tool_names,
                        {
                            "todo_doctor",
                            "todo_get_overview",
                            "todo_get_today_markdown",
                            "todo_search_tasks",
                            "todo_plan_write",
                            "todo_apply",
                        },
                    )

                    doctor_result = await session.call_tool("todo_doctor", {})
                    self.assertFalse(doctor_result.isError)
                    doctor_payload = doctor_result.structuredContent or json.loads(doctor_result.content[0].text)
                    self.assertTrue(doctor_payload["ok"])
                    self.assertEqual(doctor_payload["storage_format"], "csv")
                    self.assertIn("update_task", doctor_payload["supported_actions"])

                    overview_result = await session.call_tool("todo_get_overview", {"date": "2026-03-09"})
                    self.assertFalse(overview_result.isError)
                    overview_payload = overview_result.structuredContent or json.loads(overview_result.content[0].text)
                    self.assertTrue(overview_payload["today_archived"])
                    self.assertEqual(overview_payload["must_do_count"], 2)

                    today_result = await session.call_tool("todo_get_today_markdown", {})
                    self.assertFalse(today_result.isError)
                    today_payload = today_result.structuredContent or json.loads(today_result.content[0].text)
                    self.assertTrue(today_payload["today_exists"])
                    self.assertTrue(today_payload["today_archived"])

                    search_result = await session.call_tool(
                        "todo_search_tasks",
                        {"query": "压测", "status": ["doing", "blocked"], "limit": 10},
                    )
                    self.assertFalse(search_result.isError)
                    search_payload = search_result.structuredContent or json.loads(search_result.content[0].text)
                    self.assertEqual(search_payload["total_matches"], 1)
                    self.assertEqual(search_payload["matches"][0]["id"], "UTC-20260305-01")

                    plan_result = await session.call_tool(
                        "todo_plan_write",
                        {
                            "action": "update_task",
                            "args": {
                                "task_selector": {"id": "UTC-20260304-01"},
                                "patch": {"status": "blocked", "notes": "等待接口联调"},
                            },
                        },
                    )
                    self.assertFalse(plan_result.isError)
                    plan_payload = plan_result.structuredContent or json.loads(plan_result.content[0].text)
                    self.assertEqual(plan_payload["status"], "ready_for_confirm")
                    self.assertIn("data/tasks.csv", plan_payload["files_changed"])

                    apply_result = await session.call_tool(
                        "todo_apply",
                        {"operation_id": plan_payload["operation_id"]},
                    )
                    self.assertFalse(apply_result.isError)
                    apply_payload = apply_result.structuredContent or json.loads(apply_result.content[0].text)
                    self.assertTrue(apply_payload["ok"])
                    self.assertEqual(apply_payload["action"], "update_task")
                    self.assertIn("blocked", (self.data_repo / "data" / "tasks.csv").read_text(encoding="utf-8"))

        anyio.run(scenario)


if __name__ == "__main__":
    unittest.main()
