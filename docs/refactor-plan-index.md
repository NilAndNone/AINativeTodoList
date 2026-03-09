# Todo Codex 重构阶段索引

本文件只做阶段导航，不承载实现细节。详细要求以 `todo_codex_delivery_kit/docs/` 和对应阶段 prompt 为准。

## 当前状态

- 当前执行阶段：阶段 0 基线冻结
- 当前仓库角色：单仓版本的现有系统，作为后续分仓和服务化重构的基线
- 当前原则：先记录、先验收、再进入下一阶段

## 阶段索引

| 阶段 | 名称 | 核心目标 | 主要输出 |
| --- | --- | --- | --- |
| 0 | 基线冻结 | 固化当前可回滚状态 | baseline 文档、现状说明、测试结果 |
| 1 | 分仓与配置 | 让代码仓可以定位独立数据仓 | runtime config、doctor、split 脚本 |
| 2 | preview/apply 基础设施 | 所有写入先看 diff 再落盘 | preview runner、operation wrapper、contracts |
| 3 | MCP 只读层 | 先提供稳定的只读上下文 | doctor / overview / read tools / server skeleton |
| 4 | MCP 写入动作层 | 支持自然语言驱动主要写操作 | plan/apply、字段补问、写入工具 |
| 5 | skill + workflow + docs | 让 Codex / Claude 共享可执行 SOP | repo skill、workflow、文档 |
| 6 | 迁移、硬化、收尾 | 形成可长期维护的端到端系统 | e2e、迁移脚本、收工自动化、回滚文档 |

## 推荐阅读顺序

1. `todo_codex_delivery_kit/docs/01-目标架构.md`
2. `todo_codex_delivery_kit/docs/02-实施阶段总览.md`
3. `todo_codex_delivery_kit/docs/03-逐阶段执行与验收.md`
4. `todo_codex_delivery_kit/prompts/00-基线冻结.md`
5. 本仓库 `docs/baseline.md`

## 阶段推进规则

- 阶段验收未通过，不进入下一阶段
- 任何跨模块重构、数据契约变更、MCP 面变化，都应先对齐计划再实现
- 任何写能力都必须保留 `plan -> confirm -> apply` 语义
- `today.md` 在后续阶段仍是核心驾驶舱，不作为废弃对象处理
