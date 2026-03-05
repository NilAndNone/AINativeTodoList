# 工作流

## 事实源

| 路径 | 角色 |
| --- | --- |
| `data/tasks.csv` | 唯一长期任务状态存储 |
| `today.md` | 当天执行文件，不做长期存档 |
| `daily/YYYY-MM/WXX/YYYY-MM-DD.md` | 由 today.md 归档生成 |
| `projects/*.md` | 按项目维度的生成文件 |

## 日常操作流程

### 早上开工

确认 `today.md` 已归档或不存在后，让 agent 生成新的 `today.md`。agent 会汇报：

- 今日必须完成项（P0 / doing / 今天到期或已逾期）
- 阻塞任务
- 逾期任务

### 白天执行

口头告知 agent 进展，agent 更新 `today.md`：

| 你说的 | agent 更新的位置 |
| --- | --- |
| 任务有进展 | 对应行的 `状态` 和 `备注` |
| 新增了临时任务 | `临时新增` 表格 |
| 完成了某任务 | `实际完成` 表格 |
| 任务没做完 | `未完成 & 原因` 表格 |

### 收工归档

告诉 agent "收工"，agent 会检查 `today.md` 并列出变更摘要。你确认后 agent 执行归档。

- `doing` 任务可跨天延续，不强制收尾。
- 归档后 `today.md` 重置为归档提示。

### 周期总结

需要周报 / 月报 / 季报 / 半年报时告诉 agent，agent 生成后会摘要关键信息。

## today.md 编辑规则

对来自 `data/tasks.csv` 的已有任务，**只允许更新**：

- `状态`（todo / doing / blocked / done / cancelled）
- `备注`

以下字段**不可修改**（收工归档时按 `data/tasks.csv` 校验）：

- 标题、项目、优先级（P）、创建日期、DDL、产出

## 数据契约速查

| 项目 | 说明 |
| --- | --- |
| **CSV 字段** | `id, title, project, priority, created_date, due_date, deliverable, status, notes` |
| **合法状态** | `todo`, `doing`, `blocked`, `done`, `cancelled` |
| **合法优先级** | `P0`, `P1`, `P2`, `P3` |
| **项目代码** | `UTC`（单测客户端）、`HYP`（半年工作安排）、`TAR`（团队成员工作安排）、`HYE`（混元单测评测）、`AGE`（单测评测）、`MISC`（杂项） |
