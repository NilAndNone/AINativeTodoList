from __future__ import annotations

from pathlib import Path
import tempfile

from ainative_todo_service.config import load_runtime_config, load_data_repo_config


def test_load_runtime_and_data_repo_config() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        code_repo = root / "code"
        data_repo = root / "data-repo"
        code_repo.mkdir()
        data_repo.mkdir()

        runtime_cfg = root / "runtime.toml"
        runtime_cfg.write_text(f'data_repo = "{data_repo}"\nprofile = "default"\n', encoding="utf-8")

        data_cfg = data_repo / "todo.config.toml"
        data_cfg.write_text(
            """
schema_version = 1

[paths]
task_store = "data/tasks.csv"

[projects.UTC]
name = "单测客户端"
file = "unit-test-client.md"
focus = "focus"
""".strip() + "\n",
            encoding="utf-8",
        )

        runtime = load_runtime_config(runtime_cfg, code_repo=code_repo)
        repo_cfg = load_data_repo_config(runtime.data_repo)

        assert runtime.data_repo == data_repo.resolve()
        assert repo_cfg.schema_version == 1
        assert repo_cfg.paths["task_store"] == "data/tasks.csv"
        assert "UTC" in repo_cfg.projects
