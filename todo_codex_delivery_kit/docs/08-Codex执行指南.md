# 08 Codex 执行指南

这份指南讲的是：**你怎么让 Codex 真按这些 plan 干活**。

## 1. 推荐执行模式

### 模式 A：交互式（推荐）

适合每个阶段都想盯着看一眼：

```bash
cd /ABS/PATH/TO/CODE-REPO
codex --add-dir /ABS/PATH/TO/DATA-REPO
```

然后把 `prompts/xx-*.md` 的内容粘给 Codex。

### 模式 B：非交互式 exec

适合一个阶段一个阶段跑：

```bash
cd /ABS/PATH/TO/CODE-REPO
PROMPT_FILE="todo_codex_delivery_kit/prompts/01-分仓与配置.md"
codex exec \
  --cd /ABS/PATH/TO/CODE-REPO \
  --add-dir /ABS/PATH/TO/DATA-REPO \
  --full-auto \
  "$(cat "$PROMPT_FILE")"
```

建议每个阶段都单独执行，不要一口气把 0 到 6 全扔进去。那样很容易长出新的史诗级混沌。

## 2. 一次性准备

### 2.1 解压

把这个目录解压到**代码仓根目录**：

```text
AINativeTodoList/
  todo_codex_delivery_kit/
```

### 2.2 准备本机运行时配置

创建：

```text
~/.config/ainative-todo/config.toml
```

参考 `data_repo` 路径写好。

### 2.3 准备数据仓配置

在数据仓创建：

```text
todo.config.toml
```

可参考：

```text
todo_codex_delivery_kit/data-repo-sample/todo.config.toml.example
```

### 2.4 可选：先把示例骨架复制到目标位置

你可以手工拷贝，也可以让 Codex 干：

- `repo-overlay/src/...`
- `repo-overlay/.agents/skills/...`
- `repo-overlay/.codex/config.toml.example`
- `repo-overlay/PLANS.md`

## 3. 推荐执行顺序

### 第一步：跑阶段 0

目的：确认现状、保住 baseline。

### 第二步：跑阶段 1

目的：把 data repo、config、doctor、split script 搭出来。

### 第三步：跑阶段 2

目的：先有 preview/apply，不然所有后续写入都不稳。

### 第四步：跑阶段 3

目的：给 Codex 只读眼睛。

### 第五步：跑阶段 4

目的：给 Codex 写入手。

### 第六步：跑阶段 5

目的：让 skill、workflow、docs 真正可复用。

### 第七步：跑阶段 6

目的：收尾和 e2e。

### 最后：跑 99 整体验收

## 4. 每阶段怎么给 Codex 下达任务

每次都建议遵守这个模板：

```text
请严格执行当前阶段，不要进入下一阶段。

先阅读：
- todo_codex_delivery_kit/docs/01-目标架构.md
- todo_codex_delivery_kit/docs/02-实施阶段总览.md
- todo_codex_delivery_kit/docs/03-逐阶段执行与验收.md
- todo_codex_delivery_kit/prompts/<当前阶段文件>
- 当前仓库中的 AGENTS.md、README.md、scripts/、tests/

执行要求：
1. 只实现当前阶段范围。
2. 优先复用 todo_codex_delivery_kit/repo-overlay 中的骨架。
3. 改动完成后运行本阶段验收命令。
4. 最终回复必须包含：
   - 改了哪些文件
   - 验收结果
   - 剩余风险
   - 明确说明“未进入下一阶段”
```

## 5. 如何验收

### 代码层

看：

- 测试是否通过
- doctor 是否能输出正确路径
- preview 是否不落盘
- apply 是否真的落盘
- skill 是否可发现
- MCP 工具是否可调用

### 行为层

实际跑一轮：

- 开工
- 更新
- 新增
- 周报
- 收工

### 文档层

检查：

- 人类版 workflow
- agent 版 workflow
- tool contract
- 配置说明
- 回滚说明

## 6. 最后建议

真正使用时，**每阶段都 git commit 一次**。  
别把所有重构堆成一个巨 commit，不然回滚的时候你会体会到一种很哲学的痛苦。
