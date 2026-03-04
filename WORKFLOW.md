# 工作流

## 事实源

- 只有 `data/tasks.csv` 保存长期任务状态。
- `today.md` 是当天的执行文件，不做长期存档。
- `daily/YYYY-MM/WXX/YYYY-MM-DD.md` 由 `today.md` 归档生成。
- `projects/*.md` 和各周期 summary 都是生成文件。

## 早上

生成新的 `today.md`：

```bash
python3 scripts/todo_workflow.py generate-today
```

这个命令会读取 `data/tasks.csv`，筛出所有未关闭任务，并拆成两组：

- `今日必须完成`：`P0`、`doing`、今天到期或已经逾期的任务
- `今日计划（非必须）`：其余未关闭任务

## 白天

- 对来自 `tasks.csv` 的任务，只更新 `状态` 和 `备注`
- 临时插入的工作写到 `临时新增`
- 完成说明写到 `实际完成`
- 未完成原因和后续计划写到 `未完成 & 原因`

不要在 `today.md` 里改已有任务的标题、项目归属、优先级等字段。收工同步时会按 `data/tasks.csv` 校验这些字段。

## 收工

运行：

```bash
python3 scripts/todo_workflow.py close-day
```

这个命令会：

1. 校验 `today.md`
2. 回写已有任务的 `状态` 和 `备注`
3. 把 `临时新增` 里的任务补成正式 ID 并写回 `data/tasks.csv`
4. 将 `today.md` 归档到 `daily/YYYY-MM/WXX/YYYY-MM-DD.md`
5. 重建所有项目页
6. 将 `today.md` 重置为归档提示

## 周期总结

需要 review 文件时按需生成：

```bash
python3 scripts/todo_workflow.py generate-weekly
python3 scripts/todo_workflow.py generate-monthly
python3 scripts/todo_workflow.py generate-quarterly
python3 scripts/todo_workflow.py generate-halfyear
```

只要存在对应的 `daily` 归档记录，summary 就会尽量附上回链，方便 review 时追溯。
