# Runtime Config

## 目标

阶段 1 只解决一件事：让代码仓知道数据仓在哪里，同时把数据仓的目录契约显式化。

## 配置文件

### 本机 runtime config

默认位置：

- `~/.config/ainative-todo/config.toml`

也可以通过环境变量覆盖：

- `AINATIVE_TODO_CONFIG=/abs/path/to/config.toml`

文件示例：

```toml
profile = "default"
data_repo = "/ABS/PATH/TO/AINative_todo_data"
```

仓库内也提供了样例文件：

- `config/runtime-config.toml.example`

### 数据仓 config

数据仓根目录下需要有：

- `todo.config.toml`

当前约定至少包含：

- `[paths]`：`task_store`、`today_file`、`daily_dir`、`reports_dir`、`projects_dir`
- `[projects.*]`：项目名、项目页文件名和 focus 摘要

## 初始化数据仓

从当前单仓复制数据到独立数据仓：

```bash
python3 scripts/split_repo.py \
  --target /ABS/PATH/TO/AINative_todo_data \
  --runtime-config-out ~/.config/ainative-todo/config.toml
```

如果你确认迁移完成后要把当前代码仓清成“只剩代码”，可以显式删除源仓里的数据目录：

```bash
python3 scripts/split_repo.py \
  --target /ABS/PATH/TO/AINative_todo_data \
  --runtime-config-out ~/.config/ainative-todo/config.toml \
  --remove-source-data
```

这个开关会在复制和配置写入成功后，删除源仓顶层的：

- `data/`
- `today.md`
- `daily/`
- `reports/`
- `projects/`

如需覆盖目标目录已有文件：

```bash
python3 scripts/split_repo.py \
  --target /ABS/PATH/TO/AINative_todo_data \
  --runtime-config-out ~/.config/ainative-todo/config.toml \
  --force
```

如需直接启用 `close_day` 自动 `git commit + push`：

```bash
python3 scripts/split_repo.py \
  --target /ABS/PATH/TO/AINative_todo_data \
  --runtime-config-out ~/.config/ainative-todo/config.toml \
  --auto-commit-on-close-day \
  --auto-push-on-close-day
```

## 诊断命令

确认代码仓和数据仓配置是否连通：

```bash
python3 -m ainative_todo_service.doctor --config ~/.config/ainative-todo/config.toml
```

输出应至少包含：

- `code_repo`
- `data_repo`
- `runtime_config_path`
- `data_config_path`
- `resolved_paths`
- `git`
- `data_repo_is_git_repo`

## 旧 CLI 的使用方式

阶段 1 不改旧 CLI 的核心语义。继续通过 `--root` 指向数据仓：

```bash
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data generate-today --date 2026-03-04
```

## 本阶段边界

- 不做 preview/apply
- 不做 MCP
- 不把 `PROJECTS` 的生产读取逻辑切到配置文件
- 只建立分仓和配置契约，为下一阶段做准备
