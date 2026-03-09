# 04 MCP 工具合同

这份合同是给实现层、skill 层、测试层同时看的。关键目的只有一个：**别让工具接口变成即兴表演**。

## 总体原则

推荐不要把工具拆成二十多个零碎 action，而是维持一个稳定、可扩展的面：

- 读：少量只读工具
- 写：统一 `plan_write`
- 落地：统一 `apply`

这样 skill 逻辑会更稳，Codex 也不容易在工具海里游泳溺水。

---

## 1. todo_doctor

### 目的

确认运行时配置、数据仓路径、配置文件、git 状态、支持能力。

### 输入

```json
{}
```

### 输出示例

```json
{
  "ok": true,
  "code_repo": "/path/to/code-repo",
  "data_repo": "/path/to/data-repo",
  "runtime_config_path": "/Users/me/.config/ainative-todo/config.toml",
  "data_config_path": "/path/to/data-repo/todo.config.toml",
  "storage_format": "csv",
  "supported_actions": [
    "start_day",
    "update_task",
    "add_task",
    "mark_done",
    "mark_blocked",
    "unblock_task",
    "change_priority",
    "change_due_date",
    "cancel_task",
    "close_day",
    "generate_report",
    "rebuild_projects"
  ]
}
```

---

## 2. todo_get_overview

### 目的

给 agent 一个稳定的“今天发生了什么”的读取面。

### 输入

```json
{
  "date": "2026-03-09"
}
```

### 输出示例

```json
{
  "date": "2026-03-09",
  "today_exists": true,
  "today_archived": false,
  "must_do": [
    {
      "id": "UTC-20260304-01",
      "title": "推进性能优化",
      "project": "UTC",
      "priority": "P0",
      "due_date": "2026-03-09",
      "status": "doing",
      "notes": "等待回归验证"
    }
  ],
  "blocked": [],
  "overdue": [],
  "open_count": 8
}
```

---

## 3. todo_search_tasks

### 目的

按关键词、项目、状态、日期等过滤任务；也可用于歧义消解前的候选列举。

### 输入示例

```json
{
  "query": "性能优化",
  "project": "UTC",
  "status": ["todo", "doing", "blocked"],
  "limit": 10
}
```

### 输出示例

```json
{
  "matches": [
    {
      "id": "UTC-20260304-01",
      "title": "推进性能优化",
      "project": "UTC",
      "priority": "P0",
      "due_date": "2026-03-09",
      "status": "doing",
      "notes": "等待回归验证"
    }
  ]
}
```

---

## 4. todo_plan_write

### 目的

所有写操作统一先走这里，返回：

- 缺失字段
- 歧义候选
- preview diff
- confirm token / operation id

### 输入结构

```json
{
  "action": "update_task",
  "args": {
    "task_selector": {
      "query": "性能优化"
    },
    "patch": {
      "status": "blocked",
      "notes": "等依赖方接口"
    }
  }
}
```

### `action` 建议枚举

```text
start_day
update_task
add_task
mark_done
mark_blocked
unblock_task
change_priority
change_due_date
cancel_task
close_day
generate_report
rebuild_projects
change_project   # optional
```

### 输出状态枚举

- `needs_input`：缺字段，skill 继续追问
- `ambiguous`：候选不唯一，skill 让用户挑一个
- `ready_for_confirm`：可以展示 diff，等用户确认
- `noop`：无变化，无需写入
- `error`：参数或上下文非法

### `needs_input` 示例

```json
{
  "status": "needs_input",
  "action": "add_task",
  "missing_fields": [
    {
      "field": "priority",
      "prompt": "这个新任务的优先级是 P0 / P1 / P2 / P3 哪一个？"
    },
    {
      "field": "deliverable",
      "prompt": "预期产出是什么？"
    }
  ]
}
```

### `ambiguous` 示例

```json
{
  "status": "ambiguous",
  "action": "update_task",
  "candidates": [
    {
      "id": "UTC-20260304-01",
      "title": "推进性能优化",
      "project": "UTC",
      "status": "doing"
    },
    {
      "id": "UTC-20260305-01",
      "title": "推进性能优化二期",
      "project": "UTC",
      "status": "todo"
    }
  ],
  "prompt": "我找到了多个候选任务，请指定 ID。"
}
```

### `ready_for_confirm` 示例

```json
{
  "status": "ready_for_confirm",
  "action": "update_task",
  "operation_id": "op_20260309_0001",
  "summary": "将任务 UTC-20260304-01 的状态改为 blocked，并更新备注。",
  "files_changed": [
    "today.md",
    "data/tasks.csv"
  ],
  "diffs": [
    {
      "path": "today.md",
      "unified_diff": "--- today.md\n+++ today.md\n@@ ..."
    },
    {
      "path": "data/tasks.csv",
      "unified_diff": "--- data/tasks.csv\n+++ data/tasks.csv\n@@ ..."
    }
  ],
  "warnings": []
}
```

---

## 5. todo_apply

### 目的

只有在用户明确确认之后才调用。

### 输入

```json
{
  "operation_id": "op_20260309_0001"
}
```

### 输出

```json
{
  "ok": true,
  "action": "update_task",
  "operation_id": "op_20260309_0001",
  "applied_files": [
    "today.md",
    "data/tasks.csv"
  ],
  "post_summary": "已应用任务更新。"
}
```

---

## 6. write action 设计建议

### 6.1 start_day

#### 输入

```json
{
  "action": "start_day",
  "args": {
    "date": "2026-03-09",
    "overwrite_unarchived_today": false
  }
}
```

#### 说明

- 默认不覆盖未归档的 `today.md`
- 如发现 today 未归档，优先返回警告或 `needs_input`

### 6.2 generate_report

#### 输入

```json
{
  "action": "generate_report",
  "args": {
    "report_type": "weekly",
    "anchor_date": "2026-03-09"
  }
}
```

#### 说明

也走 preview/apply，因为它会落盘。

### 6.3 close_day

#### 输入

```json
{
  "action": "close_day",
  "args": {
    "date": "2026-03-09"
  }
}
```

#### apply 后附加行为

- 归档 today
- 重建项目页（若设计如此）
- 数据仓 git commit + push（按配置）

---

## 7. skill 层消费规则

skill / agent 必须按以下协议解释工具返回：

- `needs_input` → 只追问缺字段
- `ambiguous` → 列候选让用户选
- `ready_for_confirm` → 展示 summary + diff，等确认
- `noop` → 告诉用户无需改动
- `error` → 原样上抛，辅助定位

任何时候都不应在 `ready_for_confirm` 之前替用户做 apply。
