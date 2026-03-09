from __future__ import annotations

from dataclasses import dataclass
import difflib
from pathlib import Path
import shutil
import tempfile
from typing import Callable

from .contracts import CommandResult, DiffEntry, PreviewResult


IGNORE_NAMES = {".git", "__pycache__", ".pytest_cache", ".DS_Store"}


@dataclass(frozen=True)
class PreviewWorkspace:
    real_root: Path
    temp_root: Path


def _ignore(_dir: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORE_NAMES}


def clone_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=_ignore)


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORE_NAMES for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def diff_trees(before: Path, after: Path) -> tuple[DiffEntry, ...]:
    before_files = {path.relative_to(before).as_posix(): path for path in iter_files(before)}
    after_files = {path.relative_to(after).as_posix(): path for path in iter_files(after)}
    all_paths = sorted(set(before_files) | set(after_files))

    diffs: list[DiffEntry] = []
    for rel in all_paths:
        before_path = before_files.get(rel)
        after_path = after_files.get(rel)
        before_lines = _read_lines(before_path) if before_path else []
        after_lines = _read_lines(after_path) if after_path else []
        if before_lines == after_lines:
            continue
        diff = "".join(
            difflib.unified_diff(
                before_lines,
                after_lines,
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
            )
        )
        diffs.append(DiffEntry(path=rel, unified_diff=diff))
    return tuple(diffs)


def run_preview(
    *,
    real_root: Path,
    operation: Callable[[Path], CommandResult],
    summary: str,
) -> PreviewResult:
    resolved_root = real_root.resolve()
    with tempfile.TemporaryDirectory(prefix="todo-preview-") as temp_dir:
        temp_root = Path(temp_dir) / resolved_root.name
        clone_tree(resolved_root, temp_root)
        result = operation(temp_root)
        diffs = diff_trees(resolved_root, temp_root)
        changed_files = tuple(entry.path for entry in diffs)
        return PreviewResult(
            ok=result.ok,
            summary=summary,
            command_result=result,
            changed_files=changed_files,
            diffs=diffs,
            metadata={"temp_root": str(temp_root)},
        )
