# 开工

1. 先调用 `todo_doctor`
2. 再调用 `todo_get_overview`
3. 如果 `today.md` 未归档，先提醒用户
4. 调 `todo_plan_write(action="start_day")`
5. 展示 preview diff
6. 用户确认后调用 `todo_apply`
7. apply 后摘要：
   - must_do
   - blocked
   - overdue
