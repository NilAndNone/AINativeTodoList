# 收工

## 处理步骤

1. 调 `todo_get_overview`
2. 调 `todo_plan_write(action="close_day", args={...})`
3. 如果返回 `ready_for_confirm`，展示：
   - 归档 summary
   - `files_changed`
   - unified diff
4. 明确请求确认
5. 用户确认后调用 `todo_apply`
6. apply 成功后返回：
   - 已应用文件
   - 归档相关摘要
   - 如工具未来提供，额外返回 data repo 的 git 结果

## 注意

- `close_day` 是高影响写操作，必须明确确认
- 任何 git 自动化都只允许作用于 data repo
- 当前仓库如果还没有 git 结果回包，按现有工具输出原样汇报，不得编造 commit hash 或 push 结果
