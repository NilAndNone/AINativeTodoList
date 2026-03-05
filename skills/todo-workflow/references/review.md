# 周期总结

## 支持的报告类型

| 类型 | 命令 |
| --- | --- |
| 周报 | `python3 scripts/todo_workflow.py generate-weekly [--date YYYY-MM-DD]` |
| 月报 | `python3 scripts/todo_workflow.py generate-monthly [--date YYYY-MM-DD]` |
| 季报 | `python3 scripts/todo_workflow.py generate-quarterly [--date YYYY-MM-DD]` |
| 半年报 | `python3 scripts/todo_workflow.py generate-halfyear [--date YYYY-MM-DD]` |

`--date` 可选，默认为当天。日期用于定位所属周期（如传入某周三则生成该周的周报）。

## 流程

1. 用户要求生成报告时，调用对应命令。
2. 读取生成后的报告内容，向用户摘要关键信息：
   - 完成事项
   - 阻塞 / 风险
   - 延期 / 未完成
   - 下阶段关注点
3. 用户可要求基于报告做进一步分析。

## 报告输出路径

| 类型 | 路径 |
| --- | --- |
| 周报 | `daily/YYYY-MM/WXX/weekly-summary.md` |
| 月报 | `daily/YYYY-MM/monthly-summary.md` |
| 季报 | `daily/YYYY-QN-summary.md` |
| 半年报 | `daily/YYYY-HN-summary.md` |
