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


# 当前阶段：阶段 4 MCP 写入动作层

目标：
- 真正支持自然语言驱动 todo 写入
- 所有写入都走 `plan -> confirm -> apply`

本阶段必须支持：
- start_day
- update_task
- add_task
- mark_done
- mark_blocked
- unblock_task
- change_priority
- change_due_date
- cancel_task
- close_day
- generate_report
- rebuild_projects

关键要求：
1. 工具层必须能表达 `needs_input`
2. 工具层必须能表达 `ambiguous`
3. 工具层必须能表达 `ready_for_confirm`
4. 已有任务字段编辑能力要升级，不再只限 status / notes
5. `id` 仍然是稳定主键

建议优先参考：
- `todo_codex_delivery_kit/docs/04-MCP工具合同.md`
- `todo_codex_delivery_kit/docs/07-Agent工作流.md`

本阶段允许做的事：
- 修改数据同步契约
- 扩展 today / task 同步逻辑
- 增加更多 fixture tests

本阶段禁止做的事：
- 不做 skill 打磨
- 不做 close-day 自动 git push 之外的额外自动化

最低验收：
1. 更新已有任务可改 title / project / priority / due_date / deliverable / status / notes
2. 新增任务可缺字段补问
3. 所有写入都有 preview diff
4. 没有确认时不会 apply
