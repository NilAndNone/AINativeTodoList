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

生成今天的工作台：

```bash
python3 scripts/todo_workflow.py generate-today
```

收工时同步任务状态、归档 `today.md`，并重建项目页：

```bash
python3 scripts/todo_workflow.py close-day
```

按需生成各级总结：

```bash
python3 scripts/todo_workflow.py generate-weekly
python3 scripts/todo_workflow.py generate-monthly
python3 scripts/todo_workflow.py generate-quarterly
python3 scripts/todo_workflow.py generate-halfyear
```

完整工作流见 [WORKFLOW.md](/Users/xiaohanlu/AAAAAINativeProject/AINativeTodoList/WORKFLOW.md)。
