# 周期总结

## 支持动作

统一使用：

- `todo_plan_write(action="generate_report")`

`args.report_type` 只能是：

- `weekly`
- `monthly`
- `quarterly`
- `halfyear`

## 处理步骤

1. 提取 `report_type` 和可选 `date`
2. 调 `todo_plan_write`
3. 如果 `ready_for_confirm`：
   - 展示 summary
   - 展示报告文件 diff
   - 请求确认
4. 用户确认后 `todo_apply`
5. apply 后再读取报告或结合 diff 做摘要：
   - 完成事项
   - 阻塞 / 风险
   - 延期 / 未完成
   - 下阶段关注点

## 注意

- 生成报告会落盘，仍然属于写操作
- 没有确认前不得 apply
