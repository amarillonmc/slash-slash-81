---
description: 针对 run 的记录进行问答（command-first）
arguments: <run_id> <question>
---

目标：在当前 run 的上下文中回答问题，并记录 QA；主链路直接走 Python CLI，不依赖 custom tools。

步骤：
1. 先读取 `runs/$1/state.json` 与 `runs/$1/manifest.json`。
2. 再执行 `python -m app.cli.ask_record --run-id "$1" --question "$2"`。
3. 返回答案，并确认 `runs/$1/qa/qa.jsonl` 已追加一条记录。
4. 若 run 已 completed，回答中应包含 completion 信息；若记录不足，应显式说明不确定。
