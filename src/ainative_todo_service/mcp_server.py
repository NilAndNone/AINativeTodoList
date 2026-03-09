from __future__ import annotations

import argparse
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

from .read_api import (
    build_doctor_payload,
    build_overview_payload,
    build_today_markdown_payload,
    search_tasks_payload,
)
from .write_api import WritePlanner


def _result(payload: dict[str, object]) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))],
        structuredContent=payload,
        isError=False,
    )


def build_mcp_server(*, config_path: Path | None = None, code_repo: Path | None = None) -> FastMCP:
    resolved_code_repo = (code_repo or Path.cwd()).resolve()
    planner = WritePlanner(config_path=config_path, code_repo=resolved_code_repo)
    server = FastMCP(
        name="ainative-todo",
        instructions="AINative todo MCP tools with read access plus plan/apply write actions. All writes must go through todo_plan_write before todo_apply.",
        log_level="WARNING",
    )

    @server.tool(name="todo_doctor", description="Inspect runtime config, data repo paths, and read-only tool support.")
    def todo_doctor() -> CallToolResult:
        return _result(build_doctor_payload(config_path=config_path, code_repo=resolved_code_repo))

    @server.tool(name="todo_get_overview", description="Return a stable JSON overview of open work, blocked items, overdue items, and today metadata.")
    def todo_get_overview(date: str | None = None) -> CallToolResult:
        return _result(build_overview_payload(date=date, config_path=config_path, code_repo=resolved_code_repo))

    @server.tool(name="todo_get_today_markdown", description="Read the current today.md content and archive state without modifying any files.")
    def todo_get_today_markdown() -> CallToolResult:
        return _result(build_today_markdown_payload(config_path=config_path, code_repo=resolved_code_repo))

    @server.tool(name="todo_search_tasks", description="Search tasks by keyword, project, status, priority, and optional date filters.")
    def todo_search_tasks(
        query: str | None = None,
        project: str | None = None,
        status: list[str] | None = None,
        priority: list[str] | None = None,
        due_before: str | None = None,
        due_after: str | None = None,
        created_before: str | None = None,
        created_after: str | None = None,
        limit: int = 10,
    ) -> CallToolResult:
        return _result(
            search_tasks_payload(
                query=query,
                project=project,
                status=status,
                priority=priority,
                due_before=due_before,
                due_after=due_after,
                created_before=created_before,
                created_after=created_after,
                limit=limit,
                config_path=config_path,
                code_repo=resolved_code_repo,
            )
        )

    @server.tool(name="todo_plan_write", description="Plan a write action, returning missing fields, ambiguity candidates, or preview diffs that require explicit confirmation.")
    def todo_plan_write(action: str, args: dict[str, object] | None = None) -> CallToolResult:
        return _result(planner.plan_write(action=action, args=args))

    @server.tool(name="todo_apply", description="Apply a previously planned write operation after the user has explicitly confirmed it.")
    def todo_apply(operation_id: str) -> CallToolResult:
        return _result(planner.apply(operation_id=operation_id))

    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AINative todo MCP server.")
    parser.add_argument("--config", type=Path, default=None, help="Path to runtime config TOML")
    parser.add_argument("--code-repo", type=Path, default=Path.cwd(), help="Code repository root")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default="stdio",
        help="MCP transport to expose",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = build_mcp_server(config_path=args.config, code_repo=args.code_repo)
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
