# 工作流

## 核心原则

- `data/tasks.csv` 仍然是唯一长期事实源
- `today.md` 仍然是当天驾驶舱，但 agent 不应绕过 service 直接改文件
- 所有写操作都走：`todo_plan_write -> 看 diff -> 你确认 -> todo_apply`
- 你主要负责说自然语言和确认 diff，不负责手搓 CSV

## 事实源

| 路径 | 角色 |
| --- | --- |
| `data/tasks.csv` | 唯一长期任务状态存储 |
| `today.md` | 当天执行文件，也是 agent 的工作台视图 |
| `daily/YYYY-MM/WXX/YYYY-MM-DD.md` | 由 `today.md` 归档生成 |
| `projects/*.md` | 按项目维度的生成文件 |
| `reports/` / `daily/*summary.md` | 周 / 月 / 季 / 半年总结输出 |

## 你平时怎么用

### 开工

你说：

```text
开工
```

预期行为：

1. agent 先读 `todo_doctor` 和 `todo_get_overview`
2. 如果 `today.md` 还没归档，先提醒你选择：
   - 先收工
   - 或确认覆盖生成新的 `today.md`
3. agent 调 `todo_plan_write(action="start_day")`
4. agent 展示 `today.md` preview diff
5. 你确认后，agent 才会 `todo_apply`
6. agent 再总结今日必须项 / blocked / overdue

### 白天更新

你可以直接说自然语言，例如：

```text
把 UTC 那个性能优化任务改成 blocked，备注改成等依赖方接口。
```

```text
把 AGE 那个阶段性计划标题改成阶段性计划 v2，DDL 改到周五。
```

```text
新增一个 MISC 任务，明天下午前整理周会纪要。
```

预期行为：

1. agent 先判断对应动作：
   - `update_task`
   - `add_task`
   - `mark_done`
   - `mark_blocked`
   - `unblock_task`
   - `change_priority`
   - `change_due_date`
   - `cancel_task`
2. 缺字段时，agent 只追问缺的字段
3. 候选不唯一时，agent 列出候选任务，不瞎猜
4. 信息齐全后，agent 生成 preview diff
5. 你确认后，agent 才 apply

### 周期总结

你说：

```text
生成本周周报。
```

预期行为：

1. agent 调 `todo_plan_write(action="generate_report")`
2. agent 展示报告文件 preview diff
3. 你确认后 agent apply
4. agent 再摘要本周完成 / 风险 / 延期 / 下阶段关注点

### 收工

你说：

```text
收工
```

预期行为：

1. agent 读取 overview
2. agent 调 `todo_plan_write(action="close_day")`
3. agent 展示归档摘要和 unified diff
4. 你确认后 agent apply
5. `today.md` 归档，项目页按现有逻辑同步重建
6. 若配置启用 data repo git 自动化，则只允许作用于 data repo

## 通过 agent 可以修改什么

对已有任务，service 层支持修改：

- `title`
- `project`
- `priority`
- `due_date`
- `deliverable`
- `status`
- `notes`

新增任务时，通常至少需要补齐：

- `title`
- `project`
- `priority`
- `deliverable`
- `status`

## 手动兜底编辑规则

如果你临时手改 `today.md`，仍然遵守旧约束：

- 对来自 `data/tasks.csv` 的已有任务，只手改 `状态` 和 `备注`
- 不手改标题、项目、优先级、创建日期、DDL、产出

如果你想改这些核心字段，优先直接告诉 agent，让它走 service 的 preview/apply 流程，同时更新
`data/tasks.csv` 和 `today.md`。

## 数据契约速查

| 项目 | 说明 |
| --- | --- |
| **CSV 字段** | `id, title, project, priority, created_date, due_date, deliverable, status, notes` |
| **合法状态** | `todo`, `doing`, `blocked`, `done`, `cancelled` |
| **合法优先级** | `P0`, `P1`, `P2`, `P3` |
| **项目代码** | `UTC`（单测客户端）、`HYP`（半年工作安排）、`TAR`（团队成员工作安排）、`HYE`（混元单测评测）、`AGE`（单测评测）、`MISC`（杂项） |
