# 白天维护

## 总原则

- 任何写入一律先 `todo_plan_write`
- 优先让 service 同步更新 `data/tasks.csv` 和 `today.md`
- 不要把“手动编辑 today.md 的限制”误当成 service 的写入限制

## 更新已有任务

适用动作：

- `update_task`
- `mark_done`
- `mark_blocked`
- `unblock_task`
- `change_priority`
- `change_due_date`
- `cancel_task`

处理步骤：

1. 从自然语言提取：
   - `action`
   - `task_selector`
   - 需要更新的字段或动作参数
2. 若任务不唯一，优先用 `todo_search_tasks` 或直接让 `todo_plan_write` 返回 `ambiguous`
3. 若 `needs_input`：
   - 只按 `missing_fields` 补问
   - 补齐后重新 plan
4. 若 `ready_for_confirm`：
   - 展示 summary
   - 展示 diff
   - 等用户确认
5. 用户确认后 `todo_apply`

## 新增任务

使用 `todo_plan_write(action="add_task")`。

至少需要这些字段：

- `title`
- `project`
- `priority`
- `deliverable`
- `status`

可选字段：

- `due_date`
- `notes`
- `created_date`
- `id`

## 字段约束

对已有任务，service 支持修改：

- `title`
- `project`
- `priority`
- `due_date`
- `deliverable`
- `status`
- `notes`

## 禁止行为

- 不得直接修改 `today.md` 表格来代替工具调用
- 不得在 `ambiguous` 时自行猜测候选
- 不得在用户未确认时先 apply
