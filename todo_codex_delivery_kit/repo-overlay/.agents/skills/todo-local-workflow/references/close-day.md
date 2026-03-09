# 收工

1. 调 `todo_get_overview`
2. 调 `todo_plan_write(action="close_day")`
3. 展示：
   - 归档摘要
   - 将改动的文件
   - unified diff
4. 用户确认后 `todo_apply`
5. apply 成功后返回：
   - archive path
   - git commit / push 结果（若配置启用）

## 注意

- `close_day` 是高影响写操作，必须明确确认
- 任何 git 失败都要原样上报，不要吞错
