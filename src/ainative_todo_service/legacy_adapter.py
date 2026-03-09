from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Iterable

from .contracts import CommandResult


LEGACY_SCRIPT = Path("scripts") / "todo_workflow.py"


def build_legacy_command(
    *,
    code_repo: Path,
    data_repo: Path,
    command: str,
    date: str | None = None,
    extra_args: Iterable[str] | None = None,
) -> list[str]:
    cmd = [
        sys.executable,
        str((code_repo / LEGACY_SCRIPT).resolve()),
        "--root",
        str(data_repo.resolve()),
        command,
    ]
    if date:
        cmd.extend(["--date", date])
    if extra_args:
        cmd.extend(list(extra_args))
    return cmd


def run_legacy_command(
    *,
    code_repo: Path,
    data_repo: Path,
    command: str,
    date: str | None = None,
    extra_args: Iterable[str] | None = None,
    cwd: Path | None = None,
) -> CommandResult:
    cmd = build_legacy_command(
        code_repo=code_repo,
        data_repo=data_repo,
        command=command,
        date=date,
        extra_args=extra_args,
    )
    completed = subprocess.run(
        cmd,
        cwd=str(cwd or code_repo),
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(
        command=cmd,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
