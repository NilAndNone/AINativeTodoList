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


# 当前阶段：阶段 3 MCP 只读层

目标：
- 搭出本地 plugin/service 的最小只读能力
- 先让 Codex 能观察上下文

本阶段优先实现：
- doctor
- get_overview
- get_today_markdown
- search_tasks

建议优先参考：
- `todo_codex_delivery_kit/docs/04-MCP工具合同.md`
- `todo_codex_delivery_kit/repo-overlay/src/ainative_todo_service/mcp_tool_contracts.py`
- `todo_codex_delivery_kit/repo-overlay/.codex/config.toml.example`

本阶段允许做的事：
- 新增 MCP server skeleton 或完整实现
- 新增只读工具
- 新增 smoke tests
- 新增 Codex 配置样例

本阶段禁止做的事：
- 不做写入动作 plan/apply
- 不开始 skill 编排
- 不改变 today / close-day 语义

最低验收：
1. Codex 能发现只读工具
2. doctor / overview 工具返回稳定 JSON
3. 工具调用不写盘
