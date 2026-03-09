from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DiffEntry:
    path: str
    unified_diff: str


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class PreviewResult:
    ok: bool
    summary: str
    command_result: CommandResult
    changed_files: tuple[str, ...] = ()
    diffs: tuple[DiffEntry, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
