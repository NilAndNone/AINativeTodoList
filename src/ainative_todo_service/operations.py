from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .config import CloseDayGitConfig, ConfigError, load_data_repo_config
from .contracts import CommandResult, PreviewResult
from .git_adapter import run_close_day_git_automation
from .legacy_adapter import run_legacy_command
from .preview_runner import run_preview


class OperationError(RuntimeError):
    pass


LEGACY_REPORT_COMMANDS = {
    "weekly": "generate-weekly",
    "monthly": "generate-monthly",
    "quarterly": "generate-quarterly",
    "halfyear": "generate-halfyear",
}


def _run_real(*, code_repo: Path, data_repo: Path, command: str, date: str | None = None) -> CommandResult:
    result = run_legacy_command(
        code_repo=code_repo,
        data_repo=data_repo,
        command=command,
        date=date,
    )
    if not result.ok:
        raise OperationError(result.stderr.strip() or f"Command failed: {command}")
    return result


def preview_generate_today(*, code_repo: Path, data_repo: Path, date: str | None = None) -> PreviewResult:
    return run_preview(
        real_root=data_repo,
        summary=f"Preview legacy command: generate-today ({date or 'today'})",
        operation=lambda temp_root: run_legacy_command(
            code_repo=code_repo,
            data_repo=temp_root,
            command="generate-today",
            date=date,
        ),
    )


def apply_generate_today(*, code_repo: Path, data_repo: Path, date: str | None = None) -> CommandResult:
    return _run_real(code_repo=code_repo, data_repo=data_repo, command="generate-today", date=date)


def preview_close_day(*, code_repo: Path, data_repo: Path, date: str | None = None) -> PreviewResult:
    return run_preview(
        real_root=data_repo,
        summary=f"Preview legacy command: close-day ({date or 'today'})",
        operation=lambda temp_root: run_legacy_command(
            code_repo=code_repo,
            data_repo=temp_root,
            command="close-day",
            date=date,
        ),
    )


def apply_close_day(*, code_repo: Path, data_repo: Path, date: str | None = None) -> CommandResult:
    result = _run_real(code_repo=code_repo, data_repo=data_repo, command="close-day", date=date)
    try:
        git_config = load_data_repo_config(data_repo).git
    except ConfigError:
        git_config = CloseDayGitConfig()
    git_result = run_close_day_git_automation(
        data_repo=data_repo,
        git_config=git_config,
        date=date,
    )
    return replace(
        result,
        metadata={
            **result.metadata,
            "git": git_result,
        },
    )


def preview_generate_projects(*, code_repo: Path, data_repo: Path) -> PreviewResult:
    return run_preview(
        real_root=data_repo,
        summary="Preview legacy command: generate-projects",
        operation=lambda temp_root: run_legacy_command(
            code_repo=code_repo,
            data_repo=temp_root,
            command="generate-projects",
        ),
    )


def apply_generate_projects(*, code_repo: Path, data_repo: Path) -> CommandResult:
    return _run_real(code_repo=code_repo, data_repo=data_repo, command="generate-projects")


def preview_generate_report(*, code_repo: Path, data_repo: Path, report_type: str, date: str | None = None) -> PreviewResult:
    command = LEGACY_REPORT_COMMANDS.get(report_type)
    if command is None:
        raise OperationError(f"Unsupported report_type: {report_type}")
    return run_preview(
        real_root=data_repo,
        summary=f"Preview legacy command: {command} ({date or 'today'})",
        operation=lambda temp_root: run_legacy_command(
            code_repo=code_repo,
            data_repo=temp_root,
            command=command,
            date=date,
        ),
    )


def apply_generate_report(*, code_repo: Path, data_repo: Path, report_type: str, date: str | None = None) -> CommandResult:
    command = LEGACY_REPORT_COMMANDS.get(report_type)
    if command is None:
        raise OperationError(f"Unsupported report_type: {report_type}")
    return _run_real(code_repo=code_repo, data_repo=data_repo, command=command, date=date)
