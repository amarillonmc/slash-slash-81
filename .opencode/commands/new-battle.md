---
description: 创建新的 battle run
arguments: <rulebooks_csv> <rolesets_csv>
---

目标：创建一次新 run，生成 manifest/state。

步骤：
1. 调用 `python -m app.cli.create_run --rulebooks "$1" --rolesets "$2"`。
2. 回显 run_id 与生成路径。
3. 如需补充 manifest，可调用 tool `kb_manifest`。

注意：
- 必须通过 `boom-boom-81/kb/index/topics.jsonl` 解析规则书和角色，不可全库扫描。
