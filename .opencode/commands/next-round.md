---
description: 推进指定 run 的下一回合（command-first：自动生成+校验+state extraction+completion）
arguments: <run_id>
---

目标：一条命令完成 next-round，并且**不依赖 custom tools**。主链路必须直接调用 Python CLI，避免 tool 层损坏时出现半失败状态。

执行闭环：
1. 强制先读取 `runs/$1/state.json`。如果 `status=completed`，直接拒绝推进并返回 completion 信息。
2. 直接执行：`python -m app.cli.next_round --run-id "$1"`。
3. CLI 内部会顺序完成：
   - 读取 manifest/state/resolved KB/final rounds
   - 写入 `rounds/{n}_draft.md`
   - 执行增强 validation，输出 `rounds/{n}_validation.json`
   - 若校验通过，将 draft promote 为 `rounds/{n}_final.md`
   - 运行 state extraction / completion，更新 `state.json`
4. 返回结果：
   - 成功：`rounds/{n}_final.md` + 更新后的 `state.json`
   - 校验失败：保留 `rounds/{n}_draft.md` + `rounds/{n}_validation.json`，并明确报失败

说明：
- custom tools 当前不属于关键路径；若 OpenCode 环境仍报 `def.execute is not a function`，应继续使用本命令模板中的 CLI 主链路。
- `final` 是“通过校验并登记 state 后的正式版本”；正文通常与 draft 相同，但语义上不是“未校验草稿”。
