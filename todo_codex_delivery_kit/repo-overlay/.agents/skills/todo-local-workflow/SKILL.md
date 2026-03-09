---
name: todo-local-workflow
description: >
  管理本地 todo workflow。当用户提到开工、收工、更新任务、新增任务、
  改优先级、改 DDL、生成周报/月报/季报/半年报、重建项目页时使用。
  优先通过 ainative_todo MCP 工具执行，任何写操作必须先 preview diff，
  等待用户明确确认后再 apply。
---

# Todo Local Workflow

## 目标

让 agent 通过本地 service / MCP 工具维护 todo 系统，而不是直接绕过工具编辑文件。

## 触发意图

- 开工 / 生成 today
- 更新任务
- 新增任务
- 标记完成 / 阻塞 / 解除阻塞 / 取消
- 修改 title / project / priority / due_date / deliverable / status / notes
- 收工归档
- 生成周报 / 月报 / 季报 / 半年报
- 重建项目页

## 工具优先级

优先使用：

1. `todo_doctor`
2. `todo_get_overview`
3. `todo_search_tasks`
4. `todo_plan_write`
5. `todo_apply`

## 不变规则

- 任何写操作都必须先调用 `todo_plan_write`
- 如果返回 `needs_input`，只追问缺失字段
- 如果返回 `ambiguous`，列候选让用户选择
- 如果返回 `ready_for_confirm`，展示 summary + diff
- 在用户明确确认之前，不得调用 `todo_apply`
- `close_day` apply 后允许按配置自动 commit + push 数据仓

## 场景路由

| 场景 | 参考 |
| --- | --- |
| 开工 | [references/morning.md](references/morning.md) |
| 白天维护 | [references/during-day.md](references/during-day.md) |
| 收工归档 | [references/close-day.md](references/close-day.md) |
| 周期总结 | [references/review.md](references/review.md) |
