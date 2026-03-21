---
description: 推进指定 run 的下一回合（OpenCode tools 主路径：自动生成+校验+state extraction+completion）
arguments: <run_id>
---

目标：优先通过 OpenCode custom tools 完成 next-round；工具内部再调用 Python CLI 落盘，因此仍保持本地文件驱动与可追踪性。

执行闭环：
1. 先调用 tool `run_state` 读取 `runs/$1/state.json`。如果 `status=completed`，直接返回 completion 信息并拒绝推进。
2. 调用 tool `battle_next_round`，由工具内部执行 `python -m app.cli.next_round --run-id "$1"`。
3. 工具内部会顺序完成：
   - 读取 manifest/state/resolved KB/final rounds
   - 写入 `rounds/{n}_draft.md`
   - 执行增强 validation，输出 `rounds/{n}_validation.json`
   - 若校验通过，将 draft promote 为 `rounds/{n}_final.md`
   - 运行 state extraction / completion，更新 `state.json`
4. 返回结果：
   - 成功：`rounds/{n}_final.md` + 更新后的 `state.json`
   - 校验失败：保留 `rounds/{n}_draft.md` + `rounds/{n}_validation.json`

说明：
- custom tools 现在是 OpenCode 主路径，不再是假接通后偷偷退回“半失败”状态。
- 若需要调试，可直接执行底层 CLI，但这属于调试路径，不是默认使用说明。
