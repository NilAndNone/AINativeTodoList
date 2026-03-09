# Agent Workflow

这份文档是给 Codex / Claude 的编排层看的，不是给人类直接操作文件用的。

## 目标

通过本地 MCP 工具维护 todo 系统，避免直接编辑 `today.md`、`data/tasks.csv`、
`projects/` 或 `reports/`。

## 工具面

读取工具：

- `todo_doctor`
- `todo_get_overview`
- `todo_get_today_markdown`
- `todo_search_tasks`

写入工具：

- `todo_plan_write`
- `todo_apply`

## 支持写动作

- `start_day`
- `update_task`
- `add_task`
- `mark_done`
- `mark_blocked`
- `unblock_task`
- `change_priority`
- `change_due_date`
- `cancel_task`
- `close_day`
- `generate_report`
- `rebuild_projects`

## 全局规则

- 先判断用户请求是不是写操作
- 任何写操作都必须先 `todo_plan_write`
- 如果返回 `needs_input`，只追问 `missing_fields`
- 如果返回 `ambiguous`，展示 `candidates`，让用户明确选择
- 如果返回 `ready_for_confirm`，必须展示 `summary + files_changed + diffs`
- 没有用户明确确认，不得调用 `todo_apply`
- `noop` 直接说明无变化
- `error` 原样汇报，不擅自猜测

## 开工

触发意图：

- 开工
- 开始今天
- 生成 today

处理步骤：

1. 调 `todo_doctor`
2. 调 `todo_get_overview`
3. 若 `today_exists=true` 且 `today_archived=false`：
   - 提醒用户 `today.md` 尚未归档
   - 让用户决定先收工还是覆盖生成
4. 调 `todo_plan_write(action="start_day", args={date?, overwrite_unarchived_today?})`
5. 若 `ready_for_confirm`，展示 diff 并请求确认
6. 用户确认后调 `todo_apply`
7. apply 后摘要 must-do / blocked / overdue

## 更新与新增

支持动作：

- `update_task`
- `add_task`
- `mark_done`
- `mark_blocked`
- `unblock_task`
- `change_priority`
- `change_due_date`
- `cancel_task`

### 任务定位

优先使用：

- `task_selector.id`
- 或 `task_selector.query`
- 需要时再补 `task_selector.project`
- 需要时再补 `task_selector.status`

### 既有任务可改字段

- `title`
- `project`
- `priority`
- `due_date`
- `deliverable`
- `status`
- `notes`

### 新增任务必填

- `title`
- `project`
- `priority`
- `deliverable`
- `status`

处理步骤：

1. 从自然语言提取 `action + args`
2. 必要时可先调 `todo_search_tasks` 辅助定位
3. 调 `todo_plan_write`
4. 根据返回状态分流：
   - `needs_input`：只问缺的
   - `ambiguous`：列候选
   - `ready_for_confirm`：展示 diff
5. 用户确认后调 `todo_apply`

## 周期总结

触发意图：

- 生成周报
- 生成月报
- 生成季报
- 生成半年报

处理步骤：

1. 调 `todo_plan_write(action="generate_report", args={report_type, date?})`
2. `report_type` 只能是：
   - `weekly`
   - `monthly`
   - `quarterly`
   - `halfyear`
3. 展示 preview diff
4. 用户确认后调 `todo_apply`
5. apply 后摘要报告重点

## 收工

触发意图：

- 收工
- 下班
- 归档今天

处理步骤：

1. 调 `todo_get_overview`
2. 调 `todo_plan_write(action="close_day", args={date?})`
3. 展示归档 summary 和 diff
4. 用户确认后调 `todo_apply`
5. apply 后返回已应用文件和归档信息
6. 若工具回包包含 git 结果，只允许解释 data repo 范围内的 commit / push

## 其他写动作

`rebuild_projects`

- 用于用户明确要求重建项目页
- 仍然先 `todo_plan_write(action="rebuild_projects")`
- 展示 diff 后等待确认
- 确认后再 `todo_apply`

## 禁止行为

- 不得直接编辑文件绕过工具
- 不得把手动改 `today.md` 的限制误读成 service 限制
- 不得在候选不唯一时擅自选任务
- 不得在用户确认前提前 apply
- 不得编造工具未返回的 git 结果或归档路径
