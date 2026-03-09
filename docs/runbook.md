# Runbook

## 目标

这份 runbook 只管三件事：

1. 把旧单仓数据迁到独立 data repo
2. 验证本机 runtime config、MCP 和 CLI 都可用
3. 在需要时启用 `close_day` 的 data repo git 自动化

## 1. 迁移 data repo

```bash
python3 scripts/split_repo.py \
  --target /ABS/PATH/TO/AINative_todo_data \
  --runtime-config-out ~/.config/ainative-todo/config.toml
```

如果你已经确认 data repo 应该由 `close_day` 自动提交和推送：

```bash
python3 scripts/split_repo.py \
  --target /ABS/PATH/TO/AINative_todo_data \
  --runtime-config-out ~/.config/ainative-todo/config.toml \
  --auto-commit-on-close-day \
  --auto-push-on-close-day
```

如果目标目录已存在，需要覆盖：

```bash
python3 scripts/split_repo.py \
  --target /ABS/PATH/TO/AINative_todo_data \
  --runtime-config-out ~/.config/ainative-todo/config.toml \
  --force
```

## 2. 初始化 data repo git

只在 data repo 做，不在 code repo 做：

```bash
cd /ABS/PATH/TO/AINative_todo_data
git init
git add .
git commit -m "chore(todo): bootstrap data repo"
git remote add origin <YOUR_REMOTE>
git push -u origin HEAD
```

如果你暂时不想自动推送，就把 `todo.config.toml` 里的 `auto_push_on_close_day` 设为 `false`。

## 3. 验证运行时配置

```bash
python3 -m ainative_todo_service.doctor --config ~/.config/ainative-todo/config.toml
```

重点看：

- `data_repo` 是否是你刚迁过去的目录
- `resolved_paths` 是否都指向 data repo 内部
- `git.auto_commit_on_close_day` / `git.auto_push_on_close_day` 是否符合预期
- `data_repo_is_git_repo` 是否与当前状态一致

## 4. 本地 smoke test

CLI：

```bash
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data generate-today --date 2026-03-09
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data generate-weekly --date 2026-03-09
```

MCP server：

```bash
AINATIVE_TODO_CONFIG=~/.config/ainative-todo/config.toml \
python3 -m ainative_todo_service.mcp_server
```

## 5. close_day git 自动化行为

启用后，`todo_apply(operation_id=...)` 在 `action="close_day"` 时会：

1. 先执行归档、任务同步、项目页重建
2. 只在 data repo 内执行 `git add -A`
3. 按 `todo.config.toml` 的模板执行 `git commit`
4. 如配置启用，再执行 `git push`

返回里会带 `git` 字段：

- `git.ok`
- `git.commit_status`
- `git.commit_hash`
- `git.push_status`
- `git.error`（失败时）

## 6. 常见问题

### doctor 报 data repo 路径不对

- 检查 `~/.config/ainative-todo/config.toml`
- 确认 `data_repo = "/ABS/PATH/..."` 是绝对路径

### close_day 已归档但 git 失败

- 这是允许的部分失败形态：文件已经落盘，但 commit/push 没完成
- 直接查看 `todo_apply` 返回里的 `git.error`
- 进入 data repo 手动执行 `git status`、`git commit`、`git push`

### close_day 想只 commit 不 push

- 把 `todo.config.toml` 里的 `auto_push_on_close_day` 设为 `false`
- 保留 `auto_commit_on_close_day = true`
