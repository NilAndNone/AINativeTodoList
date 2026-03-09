# 白天维护

## 更新已有任务

- 尝试从自然语言里提取任务 selector 和 patch
- 先调 `todo_plan_write(action="update_task")`
- 如果 `needs_input`，只追问缺失字段
- 如果 `ambiguous`，列候选
- 如果 `ready_for_confirm`，展示 diff，等待确认，再 apply

## 新增任务

- 调 `todo_plan_write(action="add_task")`
- 缺字段就补问
- 不要在未确认前落盘

## 完成 / 阻塞 / 解除阻塞 / 取消

- 优先走明确 action，而不是先手工改 today.md
- 一律遵守 preview/apply
