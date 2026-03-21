---
description: 创建新的 battle run（command-first）
arguments: <rulebooks_csv> <rolesets_csv>
---

目标：创建一次新 run，生成 manifest/state，且不依赖 custom tools。

步骤：
1. 直接执行 `python -m app.cli.create_run --rulebooks "$1" --rolesets "$2"`。
2. 回显 run_id 与生成路径。
3. manifest 的解析必须来自 `boom-boom-81/kb/index/topics.jsonl`，不可全库扫描。

说明：
- 若 OpenCode custom tools 在当前环境可用，可作为可选辅助层；但创建 run 的关键路径以 CLI 为准。
