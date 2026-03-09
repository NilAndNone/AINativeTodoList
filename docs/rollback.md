# Rollback

## 适用范围

这份回滚说明只覆盖阶段 6 新增能力：

- data repo 迁移脚本补齐
- `close_day` data repo `git commit/push`
- e2e 和运行文档

不涉及下一阶段设计变更。

## 1. 最小回滚：先停掉 git 自动化

如果 `close_day` 的 git 行为有问题，先改 data repo 的 `todo.config.toml`：

```toml
[git]
auto_commit_on_close_day = false
auto_push_on_close_day = false
commit_message = "chore(todo): close day {date}"
```

这样可以保留归档和报表功能，只停掉自动 `commit/push`。

## 2. 回滚 data repo 最近一次 close_day commit

进入 data repo：

```bash
cd /ABS/PATH/TO/AINative_todo_data
git log --oneline -n 5
git revert <BAD_COMMIT>
git push
```

如果还没 push，也可以在本地直接回到上一个提交：

```bash
git reset --hard HEAD~1
```

这一步是破坏性操作，只适合你确认 data repo 最近一次提交就是错误的 `close_day` 结果。

## 3. 恢复到手动 git 流程

如果你想保留阶段 6 其他功能，只把 git 改回手动：

1. 关闭 `todo.config.toml` 里的 git 自动化
2. 继续使用 `todo_plan_write(action="close_day") -> todo_apply`
3. 归档完成后，在 data repo 手动执行：

```bash
git add -A
git commit -m "chore(todo): close day 2026-03-09"
git push
```

## 4. 回到旧 CLI 直连模式

如果 MCP 层临时不可用，旧 CLI 仍可直接驱动 data repo：

```bash
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data generate-today --date 2026-03-09
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data close-day --date 2026-03-09
```

## 5. 回退迁移配置

如果 `scripts/split_repo.py` 生成的 runtime config 不对：

1. 重新执行迁移脚本并指定正确的 `--runtime-config-out`
2. 或手动改 `~/.config/ainative-todo/config.toml`
3. 然后跑：

```bash
python3 -m ainative_todo_service.doctor --config ~/.config/ainative-todo/config.toml
```

## 6. 归档文件级回滚

如果 `today.md` 已归档，但你想恢复某一天的工作台：

```bash
cp /ABS/PATH/TO/AINative_todo_data/daily/YYYY-MM/WXX/YYYY-MM-DD.md \
   /ABS/PATH/TO/AINative_todo_data/today.md
```

然后再决定是：

- 重新编辑并再次 `close_day`
- 或直接删除这次错误归档后重新生成 `today.md`
