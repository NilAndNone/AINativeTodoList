# 开工

## 处理步骤

1. 先调用 `todo_doctor`，确认配置和 data repo 正常。
2. 调 `todo_get_overview`，确认：
   - `today_exists`
   - `today_archived`
   - `must_do`
   - `blocked`
   - `overdue`
3. 如果 `today_exists=true` 且 `today_archived=false`：
   - 先提醒用户 `today.md` 尚未归档
   - 让用户决定先 `close_day` 还是覆盖生成
   - 没有明确同意前，不得传 `overwrite_unarchived_today=true`
4. 调 `todo_plan_write(action="start_day", args={...})`
5. 若返回 `ready_for_confirm`：
   - 展示 summary
   - 展示 `today.md` diff
   - 请求用户确认
6. 用户确认后调用 `todo_apply`
7. apply 成功后，再基于 overview 摘要：
   - 今日必须项
   - blocked
   - overdue

## 注意

- 开工是写操作，必须 preview/apply，不得直接生成文件
- 如果用户只是想查看当前 `today.md`，优先调 `todo_get_today_markdown`
