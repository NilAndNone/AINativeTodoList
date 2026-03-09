---
name: todo-workflow
description: >
  兼容入口。主 skill 已迁移到 .agents/skills/todo-local-workflow/，
  用户提到开工、收工、任务更新、生成报告时，优先按新的 MCP 工具工作流执行。
---

# Todo Workflow (Legacy Alias)

主 skill 已迁移到：

- `.agents/skills/todo-local-workflow/SKILL.md`

兼容入口仍然保留，但规则以新 skill 为准：

- 优先使用 `todo_doctor`、`todo_get_overview`、`todo_get_today_markdown`、`todo_search_tasks`
- 任何写入先 `todo_plan_write`
- 看到 `needs_input` 只补问 `missing_fields`
- 看到 `ambiguous` 先让用户选候选
- 看到 `ready_for_confirm` 展示 diff，等待确认
- 没有确认不能 `todo_apply`

场景参考请改读：

- [../../.agents/skills/todo-local-workflow/references/morning.md](../../.agents/skills/todo-local-workflow/references/morning.md)
- [../../.agents/skills/todo-local-workflow/references/during-day.md](../../.agents/skills/todo-local-workflow/references/during-day.md)
- [../../.agents/skills/todo-local-workflow/references/close-day.md](../../.agents/skills/todo-local-workflow/references/close-day.md)
- [../../.agents/skills/todo-local-workflow/references/review.md](../../.agents/skills/todo-local-workflow/references/review.md)
