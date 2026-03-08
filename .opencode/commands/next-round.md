---
description: 推进指定 run 的下一回合（自动生成+校验+完结判定）
arguments: <run_id>
---

目标：一条命令完成 next-round，不要求用户手动编辑 draft。

执行闭环：
1. 强制先读取 `runs/$1/state.json`。如果 `status=completed`，直接拒绝推进并返回 completion 信息。
2. 调用 tool `battle_next_round`：
   - 自动读取 manifest/state/resolved KB/final rounds
   - 自动写入 `rounds/{n}_draft.md`（完整可校验文本，不是占位骨架）
   - 自动执行校验并 `--finalize`
   - 自动执行完成判定，必要时将 `state.status` 更新为 `completed`
3. 返回结果：
   - 成功：`rounds/{n}_final.md` + 更新后的 `state.json`
   - 校验失败：保留 `rounds/{n}_draft.md` + `rounds/{n}_validation.json`

说明：
- 当前命令无需用户额外补 prompt 或手动改 draft。
- 若需要更高质量文风，可在后续阶段增加“模型润色”步骤，但不改变本闭环自动化结果。
