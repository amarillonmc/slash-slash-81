---
description: 推进指定 run 的下一回合
arguments: <run_id>
---

目标：生成并校验下一回合。

步骤：
1. 先读取 `runs/$1/state.json`（强制）。
2. 调用 tool `battle_generate` 生成 `rounds/{n}_draft.md`。
3. 基于 `app/prompts/director_system.md` 将 draft narrative 扩写为完整回合文本并覆盖 draft。
4. 调用 tool `battle_validate`（finalize=true）完成校验与落盘。
5. 若失败，保留 draft 和 validation 报告并提示修复。

输出：
- 成功：`rounds/{n}_final.md` 与更新后的 `state.json`
- 失败：`rounds/{n}_draft.md` 与 `rounds/{n}_validation.json`
