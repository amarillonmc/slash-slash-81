---
description: 针对 run 的记录进行问答
arguments: <run_id> <question>
---

目标：在当前 run 的上下文中回答问题，并记录 QA。

步骤：
1. 读取 `runs/$1/state.json` 和 `runs/$1/manifest.json`。
2. 执行 `python -m app.cli.ask_record --run-id "$1" --question "$2"`。
3. 返回答案并确认 `runs/$1/qa/qa.jsonl` 已追加。
