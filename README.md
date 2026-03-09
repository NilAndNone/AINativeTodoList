# AINativeTodoList

基于 CSV 主表的任务管理系统，用于生成每日执行视图、项目页和便于 review 的周期总结。

## 目录说明

- `data/tasks.csv`：唯一任务事实源
- `today.md`：当天执行视图，可重复生成
- `daily/`：归档后的日记和各级总结
- `projects/`：自动生成的项目页
- `scripts/todo_workflow.py`：工作流命令行工具
- `WORKFLOW.md`：操作说明

## 快速开始

如果你还没有独立 data repo，先迁移：

```bash
python3 scripts/split_repo.py \
  --target /ABS/PATH/TO/AINative_todo_data \
  --runtime-config-out ~/.config/ainative-todo/config.toml
```

检查代码仓和数据仓是否连通：

```bash
python3 -m ainative_todo_service.doctor --config ~/.config/ainative-todo/config.toml
```

生成今天的工作台：

```bash
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data generate-today
```

收工时同步任务状态、归档 `today.md`，并重建项目页：

```bash
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data close-day
```

按需生成各级总结：

```bash
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data generate-weekly
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data generate-monthly
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data generate-quarterly
python3 scripts/todo_workflow.py --root /ABS/PATH/TO/AINative_todo_data generate-halfyear
```

如果 data repo 的 `todo.config.toml` 里启用了 `[git]`：

- `todo_plan_write(action="close_day")` 的 preview 会明确提示 `git commit/push`
- `todo_apply` 只会在 data repo 内执行 `git commit` / `git push`
- git 失败不会吞掉，返回结果里会带清晰的 `git.error`

## Agent / MCP

- 人类工作流见 [WORKFLOW.md](/Users/xiaohanlu/AAAAAINativeProject/AINativeTodoList/WORKFLOW.md)
- 独立人类版 workflow 见 [human-workflow.md](/Users/xiaohanlu/AAAAAINativeProject/AINativeTodoList/docs/human-workflow.md)
- Agent SOP 见 [docs/agent-workflow.md](/Users/xiaohanlu/AAAAAINativeProject/AINativeTodoList/docs/agent-workflow.md)
- 运行与迁移手册见 [docs/runbook.md](/Users/xiaohanlu/AAAAAINativeProject/AINativeTodoList/docs/runbook.md)
- 回滚手册见 [docs/rollback.md](/Users/xiaohanlu/AAAAAINativeProject/AINativeTodoList/docs/rollback.md)
- Codex 显式 skill 位于 [SKILL.md](/Users/xiaohanlu/AAAAAINativeProject/AINativeTodoList/.agents/skills/todo-local-workflow/SKILL.md)
- 本地 MCP server 入口：`python3 -m ainative_todo_service.mcp_server`

本仓库当前约定是：

- 读取优先使用 `todo_doctor`、`todo_get_overview`、`todo_get_today_markdown`、`todo_search_tasks`
- 任何写入都必须先 `todo_plan_write`
- 只有在用户明确确认后才能 `todo_apply`
