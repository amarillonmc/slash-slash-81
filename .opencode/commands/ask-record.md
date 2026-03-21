---
description: 针对 run 的记录进行问答（OpenCode tools 主路径）
arguments: <run_id> <question>
---

目标：通过 OpenCode 命令 + 工具链读取 run 记录、回答问题并追加 QA 记录。

步骤：
1. 先调用 tool `run_state` 读取 `runs/$1/state.json`。
2. 调用 tool `battle_ask_record`，传入 `run_id=$1`、`question=$2`。
3. 返回答案，并确认 `runs/$1/qa/qa.jsonl` 已追加一条记录。
4. 若 run 已 completed，回答中应包含 completion 信息；若记录不足，应显式说明不确定。
