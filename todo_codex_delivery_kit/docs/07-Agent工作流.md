# 07 Agent 工作流

这是给 Claude/Codex skill 和 service 编排层看的 SOP。

## 总原则

- 先判断是不是写操作
- 写操作一律先 `todo_plan_write`
- 如果缺字段，只追问缺字段
- 绝不跳过用户确认
- 所有写操作都显示 summary + diff
- 任何不可逆或高影响动作，都必须等待明确确认

## 1. 开工流程

### 触发意图

- 开工
- 开始今天
- 生成 today
- 开始维护今日任务

### 处理步骤

1. 调 `todo_doctor`
2. 调 `todo_get_overview`
3. 如果 today 未归档：
   - 提醒用户
   - 让用户决定先收工还是覆盖生成
4. 调 `todo_plan_write(action="start_day")`
5. 若 `ready_for_confirm`：
   - 展示 diff
   - 明确请求确认
6. 用户确认后调 `todo_apply`

## 2. 更新 / 新增流程

### 触发意图

- 更新任务
- 完成了
- 阻塞了
- 改 DDL
- 改优先级
- 新增任务
- 取消任务

### 处理步骤

1. 从自然语言提取 `action + args`
2. 调 `todo_plan_write`
3. 若 `needs_input`：
   - 仅按 `missing_fields` 补问
   - 补齐后再次 plan
4. 若 `ambiguous`：
   - 列候选
   - 用户选一个后再次 plan
5. 若 `ready_for_confirm`：
   - 展示 summary
   - 展示统一 diff
   - 请求确认
6. 用户确认后 apply

## 3. 周期总结流程

### 触发意图

- 生成周报 / 月报 / 季报 / 半年报

### 处理步骤

1. 调 `todo_plan_write(action="generate_report")`
2. 展示 preview diff
3. 用户确认后 apply
4. 读取落盘结果做摘要

## 4. 收工流程

### 触发意图

- 收工
- 下班
- 归档今天

### 处理步骤

1. 调 `todo_get_overview`
2. 调 `todo_plan_write(action="close_day")`
3. 展示归档摘要和 diff
4. 用户确认后 apply
5. 如配置允许：
   - 数据仓 git commit
   - 数据仓 git push
6. 返回：
   - 归档路径
   - commit hash（如有）
   - push 结果（如有）

## 5. 禁止行为

- 不得在没有 preview 的情况下直接写盘
- 不得在没有确认的情况下直接 apply
- 不得绕过 service 直接偷偷改文件
- 不得把模糊候选直接猜成某一个任务
- 不得在已知字段已经足够时继续重复追问

## 6. 错误处理

### 配置错误

- 原样上报错误
- 告诉用户缺哪个配置文件或哪个路径不存在

### 校验错误

- 原样上报具体字段问题
- 告诉用户是哪条任务、哪个字段非法

### git 错误

- 不吞错
- 分清：
  - commit 失败
  - push 失败
  - working tree 不干净
  - remote 权限问题

## 7. 风格要求

- 问最少的问题
- diff 展示尽量短，但关键信息完整
- 用户确认前，不要做“我先帮你执行了”
- 用户拒绝确认时，保留 preview 结果但不落盘
