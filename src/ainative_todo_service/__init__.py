from __future__ import annotations

from .config import ConfigError, DataRepoConfig, RuntimeConfig
from .contracts import CommandResult, DiffEntry, PreviewResult
from .mcp_tool_contracts import READ_TOOLS, WRITE_TOOLS
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
from .read_api import (
    build_doctor_payload,
    build_overview_payload,
    build_today_markdown_payload,
    search_tasks_payload,
)


def build_mcp_server(*args, **kwargs):
    from .mcp_server import build_mcp_server as _build_mcp_server

    return _build_mcp_server(*args, **kwargs)


__all__ = [
    "CommandResult",
    "ConfigError",
    "DataRepoConfig",
    "DiffEntry",
    "OperationError",
    "PreviewResult",
    "READ_TOOLS",
    "RuntimeConfig",
    "WRITE_TOOLS",
    "apply_close_day",
    "apply_generate_projects",
    "apply_generate_report",
    "apply_generate_today",
    "build_doctor_payload",
    "build_mcp_server",
    "build_overview_payload",
    "build_today_markdown_payload",
    "preview_close_day",
    "preview_generate_projects",
    "preview_generate_report",
    "preview_generate_today",
    "search_tasks_payload",
]
