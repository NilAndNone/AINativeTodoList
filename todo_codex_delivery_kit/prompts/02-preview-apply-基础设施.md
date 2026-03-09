你现在在实现一个个人使用的 todo workflow 系统重构阶段。

请严格遵守：
1. 只做当前阶段范围内的事情，不要进入下一阶段。
2. 先读：
   - todo_codex_delivery_kit/docs/01-目标架构.md
   - todo_codex_delivery_kit/docs/02-实施阶段总览.md
   - todo_codex_delivery_kit/docs/03-逐阶段执行与验收.md
   - 当前阶段 prompt 文件本身
   - 当前仓库的 AGENTS.md、README.md、WORKFLOW.md、scripts/、tests/
3. 优先复用 `todo_codex_delivery_kit/repo-overlay/` 里的示例结构和代码骨架，但必须根据当前仓库真实情况调整，不要机械照抄。
4. 修改完成后，运行当前阶段要求的测试和命令。
5. 最终回复必须包含：
   - 本阶段改动文件列表
   - 已运行的命令
   - 验收是否通过
   - 剩余风险
   - 明确说明“未进入下一阶段”


# 当前阶段：阶段 2 preview/apply 基础设施

目标：
- 为所有现有落盘命令建立 preview/apply 层
- preview 不触碰真实数据仓
- apply 落盘结果与 preview diff 一致

建议优先参考：
- `todo_codex_delivery_kit/repo-overlay/src/ainative_todo_service/contracts.py`
- `todo_codex_delivery_kit/repo-overlay/src/ainative_todo_service/preview_runner.py`
- `todo_codex_delivery_kit/repo-overlay/src/ainative_todo_service/legacy_adapter.py`
- `todo_codex_delivery_kit/repo-overlay/src/ainative_todo_service/operations.py`

本阶段至少接管：
- generate-today
- close-day
- generate-weekly
- generate-monthly
- generate-quarterly
- generate-halfyear
- generate-projects

本阶段允许做的事：
- 新增 preview/apply 抽象
- 新增 unified diff 生成
- 新增 operation wrappers
- 补测试

本阶段禁止做的事：
- 不做 MCP server
- 不做自然语言写入动作
- 不修改项目配置来源之外的业务逻辑

最低验收：
1. preview 后真实 data repo 无变化
2. apply 后变化与 preview diff 一致
3. 测试覆盖至少包括 `generate-today` 与 `close-day`
