---
name: todo-local-workflow
description: >
  管理本地 todo workflow。当用户提到开工、收工、更新任务、新增任务、
  改优先级、改 DDL、改标题、生成周报/月报/季报/半年报、重建项目页时使用。
  优先通过 ainative_todo MCP 工具执行，任何写操作必须先 preview diff，
  等待用户明确确认后再 apply。
---

# Todo Local Workflow

## 何时触发

以下意图应显式使用本 skill：

- 开工 / 开始今天 / 生成 today
- 更新已有任务
- 新增任务
- 标记完成 / 阻塞 / 解除阻塞 / 取消
- 修改 `title / project / priority / due_date / deliverable / status / notes`
- 收工归档
- 生成周报 / 月报 / 季报 / 半年报
- 重建项目页

## 目标

让 agent 通过本地 service / MCP 工具维护 todo 系统，而不是直接绕过工具编辑
`today.md`、`data/tasks.csv`、`projects/` 或 `reports/`。

## 工具顺序

优先使用：

1. `todo_doctor`
2. `todo_get_overview`
3. `todo_get_today_markdown`
4. `todo_search_tasks`
5. `todo_plan_write`
6. `todo_apply`

## 写入协议

所有写入都遵守同一协议：

1. 判断意图对应的 `action`
2. 调 `todo_plan_write(action=..., args=...)`
3. 根据返回状态分流：
   - `needs_input`：只按 `missing_fields` 追问缺失字段
   - `ambiguous`：展示 `candidates`，让用户明确选择
   - `ready_for_confirm`：展示 `summary + files_changed + diffs`
   - `noop`：说明无实际变化，不再 apply
   - `error`：原样转述错误，不擅自猜测修复
4. 只有在用户明确确认后，才能调 `todo_apply(operation_id=...)`

## 关键合同

- 对已有任务，service 允许修改：
  - `title`
  - `project`
  - `priority`
  - `due_date`
  - `deliverable`
  - `status`
  - `notes`
- `add_task` 至少需要补齐：
  - `title`
  - `project`
  - `priority`
  - `deliverable`
  - `status`
- 任务定位优先用：
  - `task_selector.id`
  - 或 `task_selector.query`
  - 需要时再补 `project` / `status`
- `generate_report` 的 `report_type` 只能是：
  - `weekly`
  - `monthly`
  - `quarterly`
  - `halfyear`
- `start_day` 遇到未归档 `today.md` 时，不得默认覆盖；只有用户确认后才能传
  `overwrite_unarchived_today=true`

## 不变规则

- 不得直接编辑文件来绕过 MCP 工具
- 不得在没有 preview diff 的情况下直接写盘
- 不得在没有明确确认的情况下调用 `todo_apply`
- 不得把模糊候选直接猜成某个任务
- 不得在字段已足够时重复追问
- `close_day` 若后续配置启用 git 自动化，也只允许作用于 data repo；当前回包以工具实际返回为准

## 场景路由

| 场景 | 参考 |
| --- | --- |
| 开工 | [references/morning.md](references/morning.md) |
| 白天维护 | [references/during-day.md](references/during-day.md) |
| 收工归档 | [references/close-day.md](references/close-day.md) |
| 周期总结 | [references/review.md](references/review.md) |
