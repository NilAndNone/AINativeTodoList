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


# 当前阶段：阶段 5 skill / 文档 / workflow

目标：
- 把 Codex 真正教会怎么使用这套本地 service

本阶段必须落地：
- `.agents/skills/todo-local-workflow/`
- `SKILL.md`
- `references/`
- 人类版 workflow
- agent 版 workflow

建议优先参考：
- `todo_codex_delivery_kit/repo-overlay/.agents/skills/todo-local-workflow/`
- `todo_codex_delivery_kit/docs/06-人类工作流.md`
- `todo_codex_delivery_kit/docs/07-Agent工作流.md`

关键要求：
1. skill 必须优先用工具，而不是直接编辑文件
2. 任何写入先 `todo_plan_write`
3. 看到 `missing_fields` 就补问
4. 看到 `ready_for_confirm` 就展示 diff
5. 没有用户确认不能 apply

最低验收：
1. skill 能显式触发
2. 文档与工具合同一致
3. 用户版和 agent 版 workflow 不互相冲突
