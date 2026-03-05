# 早上开工

## 流程

1. **读取 `data/tasks.csv`**，检查遗留的 `doing` / `blocked` 任务。

2. **检查 `today.md` 状态**：
   - 若 `today.md` 不存在：视为首次开工，直接继续。
   - 若 `today.md` 含 "已归档" 标记：正常，直接继续。
   - 若 `today.md` 未归档（仍有当天任务内容）：**停下**，提醒用户选择：
     - "先收工"（转到 close-day 流程）
     - "确认覆盖生成新的 today.md"

3. **调用命令生成 today.md**：
   ```bash
   python3 scripts/todo_workflow.py generate-today
   ```

4. **读取生成后的 `today.md`**，向用户汇报：
   - 今日必须完成项（P0 / doing / 今天到期或已逾期）
   - 阻塞任务
   - 逾期任务

## 约束

- 不自动决定优先级变更。
- 不自动修改 `data/tasks.csv`。
- 仅汇报，由用户决定后续行动。
