# Human Workflow

这份文档是给你自己看的极简使用说明，不是给 agent 编排层看的。

## 核心原则

- 你主要发自然语言，不直接手改 CSV
- agent 通过本地 MCP 工具维护 todo 系统
- 所有写操作都遵守：`todo_plan_write -> 看 diff -> 你确认 -> todo_apply`
- `data/tasks.csv` 是唯一长期事实源
- `today.md` 仍然是当天驾驶舱

## 开工

你说：

```text
开工
```

预期行为：

1. agent 先读取 `todo_doctor` 和 `todo_get_overview`
2. 若 `today.md` 未归档，提醒你先收工或确认覆盖
3. agent 调 `todo_plan_write(action="start_day")`
4. agent 展示 `today.md` preview diff
5. 你确认
6. agent 调 `todo_apply`
7. agent 摘要今日必须项 / blocked / overdue

## 白天更新

### 更新既有任务

你说：

```text
把 UTC 那个性能优化任务改成 blocked，备注改成等依赖方接口。
```

或：

```text
把 AGE 那个阶段性计划标题改成阶段性计划 v2，DDL 改到周五。
```

预期行为：

1. agent 定位任务
2. 若有歧义，列候选
3. 若缺字段，只追问缺失字段
4. agent 生成 diff
5. 你确认
6. agent apply

### 新增任务

你说：

```text
新增一个 MISC 任务，明天下午前整理周会纪要。
```

预期行为：

1. agent 补齐必要字段
2. agent 生成 diff
3. 你确认
4. agent apply

## 通过 agent 可以修改什么

对已有任务，service 层支持修改：

- `title`
- `project`
- `priority`
- `due_date`
- `deliverable`
- `status`
- `notes`

## 周期总结

你说：

```text
生成本周周报。
```

预期行为：

1. agent 调 `todo_plan_write(action="generate_report")`
2. 展示报告 preview diff
3. 你确认
4. agent apply
5. agent 摘要完成事项 / 风险 / 延期 / 下阶段关注点

## 收工

你说：

```text
收工
```

预期行为：

1. agent 读取 `today` 和 overview
2. agent 调 `todo_plan_write(action="close_day")`
3. 展示归档摘要和 diff
4. 你确认
5. agent apply
6. 如配置启用，只允许在 data repo 做 git 自动化

## 手动兜底规则

如果你临时手改 `today.md`：

- 对来自 `data/tasks.csv` 的已有任务，只手改 `状态` 和 `备注`
- 不手改标题、项目、优先级、创建日期、DDL、产出

如果你要改这些核心字段，优先直接告诉 agent，让它走 service 的 preview/apply 流程。
