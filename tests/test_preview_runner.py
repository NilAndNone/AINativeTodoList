from __future__ import annotations

from pathlib import Path
import tempfile

from ainative_todo_service.contracts import CommandResult
from ainative_todo_service.preview_runner import run_preview


def test_run_preview_does_not_modify_real_root() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        real_root = root / "real"
        real_root.mkdir()
        (real_root / "today.md").write_text("old\n", encoding="utf-8")

        def operation(temp_root: Path) -> CommandResult:
            (temp_root / "today.md").write_text("new\n", encoding="utf-8")
            return CommandResult(
                command=["fake"],
                returncode=0,
                stdout="ok",
                stderr="",
            )

        result = run_preview(real_root=real_root, operation=operation, summary="preview test")

        assert (real_root / "today.md").read_text(encoding="utf-8") == "old\n"
        assert result.ok is True
        assert result.changed_files == ("today.md",)
        assert "a/today.md" in result.diffs[0].unified_diff
        assert "b/today.md" in result.diffs[0].unified_diff
