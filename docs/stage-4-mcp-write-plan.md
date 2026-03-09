# 阶段 4 MCP 写入动作层执行计划

## 背景

当前仓库已经有：

- 运行时配置与数据仓定位
- preview/apply 基础设施
- MCP 只读层

但写操作仍缺少统一的 `plan -> confirm -> apply` 合同，且 `close-day` 只接受已有任务的 `状态` 和 `备注` 变更，不能支撑阶段 4 所需的自然语言写入能力。

## 范围

- 为 MCP server 增加 `todo_plan_write` 和 `todo_apply`
- 支持阶段 4 要求的写动作：
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
- 升级 today/CSV 同步契约，让已有任务可更新：
  - `title`
  - `project`
  - `priority`
  - `due_date`
  - `deliverable`
  - `status`
  - `notes`
- 增加针对 `needs_input`、`ambiguous`、`ready_for_confirm`、preview/apply 的测试

## 非范围

- 不进入阶段 5 的 skill 打磨、workflow 文档重写
- 不进入阶段 6 的 close-day git 自动化、e2e 收尾
- 不做新的远程服务部署或存储格式迁移

## 输入输出

### 输入

- MCP `todo_plan_write(action, args)`
- MCP `todo_apply(operation_id)`
- 现有数据仓配置和 CSV/today 文件结构

### 输出

- 稳定的 MCP 写入工具合同
- 带 preview diff 的计划结果
- 仅在确认后才执行的 apply 结果
- today/CSV 同步契约升级后的行为与测试

## 变更文件

- `docs/refactor-plan-index.md`
- `scripts/todo_workflow.py`
- `src/ainative_todo_service/doctor.py`
- `src/ainative_todo_service/mcp_server.py`
- `src/ainative_todo_service/mcp_tool_contracts.py`
- `src/ainative_todo_service/read_api.py`
- `src/ainative_todo_service/write_api.py`
- `src/ainative_todo_service/__init__.py`
- `ainative_todo_service/__init__.py`
- `tests/test_mcp_server.py`
- `tests/test_todo_workflow.py`
- `tests/test_write_api.py`

## 验收命令

```bash
python3 -m pytest tests/test_todo_workflow.py
python3 -m pytest tests/test_write_api.py
python3 -m pytest tests/test_mcp_server.py
python3 -m pytest tests/
```

## 风险与回滚

- 风险：
  - today 文件重写会规范化现有表格格式
  - 写入计划结果目前保存在 MCP server 进程内，重启后 operation id 失效
  - `add_task` 写入 today 时采用“带 ID 的今日任务行”而非旧的纯手工 `临时新增` 同步路径
- 回滚：
  - 代码层可回退本阶段修改
  - 数据层写入仍受 `plan -> confirm -> apply` 约束，未确认不会落盘
