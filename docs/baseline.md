# 阶段 0 Baseline

## 快照信息

- 冻结日期：2026-03-09
- Git 分支：`feature/0309-refactor`
- Git 提交：`e069633e1c4ee71e18e02f53a2f53c91c8156de2`
- 当前阶段：阶段 0 基线冻结
- 阶段目标：记录现状、验证现有测试、为后续重构保留可对照基线

## 当前仓库结构

当前仓库仍是代码与数据同仓：

- `scripts/todo_workflow.py`：单体 CLI，承载 today、归档、项目页、周期报告的全部主逻辑
- `tests/test_todo_workflow.py`：现有自动化回归测试
- `data/tasks.csv`：唯一长期事实源
- `today.md`：当天执行驾驶舱
- `daily/`：日归档与周期总结输出目录
- `projects/`：按项目生成的 Markdown 页面
- `reports/templates/`：周报、月报、季报、半年报模板
- `todo_codex_delivery_kit/`：本轮重构交付说明、阶段 prompt 与 overlay 参考

## 当前 CLI 命令面

`scripts/todo_workflow.py` 当前暴露以下命令，并统一支持隐藏参数 `--root` 指向仓库根：

- `generate-today [--date YYYY-MM-DD]`
- `close-day [--date YYYY-MM-DD]`
- `generate-weekly [--date YYYY-MM-DD]`
- `generate-monthly [--date YYYY-MM-DD]`
- `generate-quarterly [--date YYYY-MM-DD]`
- `generate-halfyear [--date YYYY-MM-DD]`
- `generate-projects`

## 当前行为基线

### 数据契约

- CSV 字段固定为 `id,title,project,priority,created_date,due_date,deliverable,status,notes`
- `id` 是稳定主键
- 合法状态：`todo`、`doing`、`blocked`、`done`、`cancelled`
- 合法优先级：`P0`、`P1`、`P2`、`P3`

### `generate-today`

- 从 `data/tasks.csv` 读取任务
- 按优先级、DDL、项目、ID 排序开放任务
- 将 `doing`、`P0`、当日到期或逾期任务放入“今日必须完成”
- 其余开放任务放入“今日计划（非必须）”
- 固定生成“临时新增”“实际完成”“未完成 & 原因”“备注”区块

### `close-day`

- 从 `today.md` 回读“今日必须完成”“今日计划（非必须）”两张任务表
- 只接受已有任务的 `状态` 与 `备注` 变更
- 对已有任务会校验以下字段不可变：`标题`、`项目`、`P`、`创建`、`DDL`、`产出`
- 允许通过“临时新增”创建新任务并回写到 `data/tasks.csv`
- 允许通过“实际完成”将任务标记为 `done`
- 归档 `today.md` 到 `daily/YYYY-MM/WXX/YYYY-MM-DD.md`
- 归档后重写 `today.md` 为已归档提示，并重建全部项目页

### 周期总结与项目页

- 周报、月报、季报、半年报均由当前 CLI 直接生成 Markdown 输出
- 项目页由代码内 `PROJECTS` 映射驱动，输出到 `projects/*.md`
- 当前仓库已有 6 个项目页生成目标：`UTC`、`HYP`、`TAR`、`HYE`、`AGE`、`MISC`

## 当前数据与工作台现状

以冻结时仓库内容为准：

- `data/tasks.csv` 当前共有 18 条任务
- 状态分布：`doing=1`、`todo=16`、`blocked=1`
- 项目分布：`UTC=5`、`HYP=3`、`TAR=2`、`HYE=3`、`AGE=4`、`MISC=1`
- `today.md` 当前存在，日期头为 `2026-03-04`
- `projects/` 当前已有 6 个生成页面
- `daily/` 当前没有已归档日记录文件

## 当前测试基线

现有自动化测试集中在 `tests/test_todo_workflow.py`，覆盖：

- `generate-today` 对开放任务的分栏行为
- `close-day` 对 CSV 回写、归档与项目页重建的主路径
- `generate-weekly` 对周报来源链接与内容片段的生成

阶段 0 只允许验证这些既有能力，不扩展生产逻辑和数据契约。

## 已知限制

后续阶段必须以这些现状为重构起点：

- 项目映射写死在 `scripts/todo_workflow.py`
- 已有任务在 `today.md` 中只允许改 `状态` 和 `备注`
- 数据与代码仍在同一个仓库内
- Codex 当前没有正式的 plugin / service / MCP 执行层

## 本阶段非目标

以下内容在阶段 0 明确不做：

- 不改 `scripts/todo_workflow.py` 的生产行为
- 不改 CSV 与 `today.md` 的现有数据契约
- 不引入 MCP
- 不开始代码仓 / 数据仓拆分
