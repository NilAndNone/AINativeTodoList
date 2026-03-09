# Todo Codex 补充指令片段

把下面这段并入仓库根 `AGENTS.md` 即可：

---

## Todo system migration rules

When a task touches the todo workflow architecture, MCP tools, repo split, config design, or the data contract, use an ExecPlan from `PLANS.md` and stay within one phase at a time.

### Hard rules

- Preserve `plan -> confirm -> apply` for every write operation.
- Keep `today.md` as the primary day workbench.
- Treat `id` as the stable task primary key.
- Prefer configuration in the data repo over hard-coded project mappings.
- Prefer compatibility wrappers around the legacy CLI before replacing behavior.
- Do not silently write to the data repo without a preview diff.
- Do not auto-confirm writes.
- Only `close_day` may default to auto `git commit + push`, and that behavior must be configurable and test-covered.
