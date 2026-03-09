# Todo Codex Delivery Kit

这是一份**直接面向 Codex 执行**的重构包，目标是把你当前的 `AINativeTodoList` 演进成：

- **代码仓 / 数据仓解耦**
- **统一本地 plugin/service（推荐落成 MCP server）**
- **Claude Code / Codex 共用同一执行内核**
- **所有写操作先 preview diff，再 confirm，再 apply**
- **agent 围绕 `today.md` 工作**
- **收工自动 commit + push（仅数据仓）**

这份包不是“已经帮你改好仓库”的成品，而是三层东西叠在一起：

1. **可让 Codex 分阶段执行的计划文档**
2. **可以直接复制/改造的示例配置与代码骨架**
3. **给 Codex 喂的现成 prompts**

## 目录

- `docs/`：设计、阶段计划、验收、工作流
- `prompts/`：每一阶段直接喂给 Codex 的提示词
- `repo-overlay/`：代码仓建议新增的文件骨架
- `data-repo-sample/`：数据仓配置样例

## 你应该怎么用

1. 把整个目录解压到**代码仓根目录**，例如：
   - `/path/to/AINativeTodoList/todo_codex_delivery_kit/`
2. 先看 `docs/08-Codex执行指南.md`
3. 按顺序执行：
   - `prompts/00-基线冻结.md`
   - `prompts/01-分仓与配置.md`
   - `prompts/02-preview-apply-基础设施.md`
   - `prompts/03-MCP-只读层.md`
   - `prompts/04-MCP-写入动作层.md`
   - `prompts/05-skill-文档-工作流.md`
   - `prompts/06-迁移-硬化-收尾.md`
   - `prompts/99-整体验收.md`

## 这份包里哪些东西是“可直接运行”的

下面这些是**示例但可运行**的：

- `repo-overlay/src/ainative_todo_service/config.py`
- `repo-overlay/src/ainative_todo_service/legacy_adapter.py`
- `repo-overlay/src/ainative_todo_service/preview_runner.py`
- `repo-overlay/src/ainative_todo_service/operations.py`
- `repo-overlay/src/ainative_todo_service/doctor.py`
- `repo-overlay/scripts/split_repo_example.py`

下面这些是**协议 / 骨架**，需要 Codex 按计划真正实现：

- `repo-overlay/src/ainative_todo_service/mcp_tool_contracts.py`
- `repo-overlay/.agents/skills/todo-local-workflow/*`
- `repo-overlay/.codex/config.toml.example`

## 当前方案的关键决策

- **任务事实源 v1 继续使用 CSV**，先保留兼容性，别在第一刀就去追求“完美格式”。宇宙已经够混乱了。
- **配置统一改为 TOML**，因为 Python 标准库 `tomllib` 就能读，省掉 YAML 依赖包。
- **自然语言写操作走统一 preview/apply 两段式**
- **`id` 保持稳定主键，不作为日常字段修改**
- **项目映射移出代码，进入数据仓配置**
- **只有收工默认自动 git commit + push**

## 建议落地顺序

先把**分仓 + preview/apply + 兼容旧 CLI**搭起来，再做 MCP，再做 skill，再做细颗粒写入动作。不要一上来就把所有东西炖成架构火锅。
