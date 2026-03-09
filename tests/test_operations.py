from __future__ import annotations

from pathlib import Path
import shutil
import tempfile

from ainative_todo_service.operations import apply_close_day, apply_generate_today, preview_close_day, preview_generate_today
from ainative_todo_service.preview_runner import diff_trees


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


TASKS_CSV = "\n".join(
    [
        "id,title,project,priority,created_date,due_date,deliverable,status,notes",
        "UTC-20260304-01,推进性能优化,UTC,P0,2026-03-04,2026-03-06,分析报告,doing,当前在推进",
        "AGE-20260304-01,输出阶段性计划文档,AGE,P1,2026-03-04,,阶段性计划文档,todo,待开始",
        "MISC-20260304-01,处理临时支持,MISC,P2,2026-03-04,,沟通记录,todo,记录杂项",
    ]
) + "\n"


TODAY_MARKDOWN = "\n".join(
    [
        "# 2026-03-04 周三",
        "",
        "## 今日必须完成",
        "",
        "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "| UTC-20260304-01 | 推进性能优化 | UTC | P0 | 2026-03-04 | 2026-03-06 | 分析报告 | doing | 当天补齐性能回归 |",
        "",
        "## 今日计划（非必须）",
        "",
        "| ID | 标题 | 项目 | P | 创建 | DDL | 产出 | 状态 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "| AGE-20260304-01 | 输出阶段性计划文档 | AGE | P1 | 2026-03-04 |  | 阶段性计划文档 | todo | 待开始 |",
        "",
        "## 临时新增",
        "",
        "| 标题 | 项目 | P | DDL | 产出 | 状态 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        "| 处理临时评审反馈 | MISC | P1 | 2026-03-04 | 评审纪要 | done | 当天插入 |",
        "",
        "## 实际完成",
        "",
        "| ID | 标题 | 完成情况 |",
        "| --- | --- | --- |",
        "| UTC-20260304-01 | 推进性能优化 | 完成主要回归验证 |",
        "|  | 处理临时评审反馈 | 评审反馈已同步 |",
        "",
        "## 未完成 & 原因",
        "",
        "| ID | 标题 | 原因 | 后续计划 |",
        "| --- | --- | --- | --- |",
        "| AGE-20260304-01 | 输出阶段性计划文档 | 还在补背景 | 明天继续 |",
        "",
        "## 备注",
        "",
        "今天主要收敛了性能相关事项。",
        "",
    ]
)


def create_data_repo(root: Path) -> Path:
    data_repo = root / "data_repo"
    write_file(data_repo / "data" / "tasks.csv", TASKS_CSV)
    return data_repo


def clone_snapshot(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def diff_map(before: Path, after: Path) -> dict[str, str]:
    return {entry.path: entry.unified_diff for entry in diff_trees(before, after)}


def test_preview_generate_today_does_not_modify_real_repo_and_apply_matches_diff() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        data_repo = create_data_repo(root)
        before = root / "before"
        clone_snapshot(data_repo, before)

        preview = preview_generate_today(code_repo=REPO_ROOT, data_repo=data_repo, date="2026-03-04")

        assert preview.ok is True
        assert not (data_repo / "today.md").exists()
        assert preview.changed_files == ("today.md",)
        assert "## 今日必须完成" in preview.diffs[0].unified_diff
        assert "UTC-20260304-01" in preview.diffs[0].unified_diff
        assert "AGE-20260304-01" in preview.diffs[0].unified_diff

        apply_result = apply_generate_today(code_repo=REPO_ROOT, data_repo=data_repo, date="2026-03-04")

        assert apply_result.ok is True
        assert (data_repo / "today.md").exists()
        today_text = (data_repo / "today.md").read_text(encoding="utf-8")
        assert "## 今日必须完成" in today_text
        assert "UTC-20260304-01" in today_text
        assert diff_map(before, data_repo) == {entry.path: entry.unified_diff for entry in preview.diffs}


def test_preview_close_day_does_not_modify_real_repo_and_apply_matches_diff() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        data_repo = create_data_repo(root)
        write_file(data_repo / "today.md", TODAY_MARKDOWN)
        before = root / "before"
        clone_snapshot(data_repo, before)

        preview = preview_close_day(code_repo=REPO_ROOT, data_repo=data_repo, date="2026-03-04")

        assert preview.ok is True
        assert (data_repo / "today.md").read_text(encoding="utf-8") == TODAY_MARKDOWN
        assert not (data_repo / "daily" / "2026-03" / "W10" / "2026-03-04.md").exists()
        assert not (data_repo / "projects" / "unit-test-client.md").exists()
        assert "data/tasks.csv" in preview.changed_files
        assert "today.md" in preview.changed_files
        assert "daily/2026-03/W10/2026-03-04.md" in preview.changed_files
        assert "projects/unit-test-client.md" in preview.changed_files

        apply_result = apply_close_day(code_repo=REPO_ROOT, data_repo=data_repo, date="2026-03-04")

        assert apply_result.ok is True
        assert (data_repo / "daily" / "2026-03" / "W10" / "2026-03-04.md").exists()
        assert (data_repo / "projects" / "unit-test-client.md").exists()
        assert diff_map(before, data_repo) == {entry.path: entry.unified_diff for entry in preview.diffs}
