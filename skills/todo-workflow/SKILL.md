---
name: todo-workflow
description: >
  管理每日任务工作流。当用户提到"开工""收工""任务更新""生成报告"
  或操作 today.md / tasks.csv 时触发。根据场景按需加载
  morning / during-day / close-day / review 参考文档。
---

# Todo Workflow

## 工作流总览

本 skill 指导 agent 操作任务管理系统。agent 是主要驱动者，`scripts/todo_workflow.py` 作为工具被调用。

### 事实源

| 路径 | 角色 |
| --- | --- |
| `data/tasks.csv` | 唯一长期任务状态存储 |
| `today.md` | 当天执行文件，不做长期存档 |
| `daily/YYYY-MM/WXX/YYYY-MM-DD.md` | 由 today.md 归档生成 |
| `projects/*.md` | 按项目维度的生成文件 |

### 数据契约速查

- CSV 字段：`id, title, project, priority, created_date, due_date, deliverable, status, notes`
- 合法状态：`todo`, `doing`, `blocked`, `done`, `cancelled`
- 合法优先级：`P0`, `P1`, `P2`, `P3`
- 项目代码：`UTC`（单测客户端）、`HYP`（半年工作安排）、`TAR`（团队成员工作安排）、`HYE`（混元单测评测）、`AGE`（单测评测）、`MISC`（杂项）

### 项目代码映射

| 项目代码 | 名称 | 关注范围 |
| --- | --- | --- |
| UTC | 单测客户端 | 客户端工程实现、稳定性、性能、监控与离线流程建设 |
| HYP | 半年工作安排 | 未来半年的工作主线、阶段性交付节奏与整体规划口径 |
| TAR | 团队成员工作安排 | 个人工作安排与团队成员承接方向的阶段性拆解 |
| HYE | 混元单测评测 | 模型评测事项记录、整理与边界维护 |
| AGE | 单测评测 | 单元测试代码生成 agent 的评测框架与阶段性输出 |
| MISC | 杂项 | 临时支持、会议、沟通和跨项目事项 |

## 场景路由

根据用户意图加载对应参考文档：

| 场景 | 触发词 | 参考文档 |
| --- | --- | --- |
| 早上开工 | "开工"、"开始今天"、"生成 today" | [references/morning.md](references/morning.md) |
| 白天执行 | "更新任务"、"新增任务"、"完成了"、"没做完" | [references/during-day.md](references/during-day.md) |
| 收工归档 | "收工"、"下班"、"归档" | [references/close-day.md](references/close-day.md) |
| 周期总结 | "周报"、"月报"、"季报"、"半年报" | [references/review.md](references/review.md) |

## 命令速查

所有命令须在仓库根目录执行。

```bash
# 生成今日工作文件
python3 scripts/todo_workflow.py generate-today [--date YYYY-MM-DD]

# 收工归档
python3 scripts/todo_workflow.py close-day [--date YYYY-MM-DD]

# 周期报告
python3 scripts/todo_workflow.py generate-weekly [--date YYYY-MM-DD]
python3 scripts/todo_workflow.py generate-monthly [--date YYYY-MM-DD]
python3 scripts/todo_workflow.py generate-quarterly [--date YYYY-MM-DD]
python3 scripts/todo_workflow.py generate-halfyear [--date YYYY-MM-DD]

# 重建项目页
python3 scripts/todo_workflow.py generate-projects
```
