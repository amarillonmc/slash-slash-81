---
description: 创建新的 battle run（OpenCode tools 主路径）
arguments: <rulebooks_csv> <rolesets_csv>
---

目标：创建一次新 run，生成 manifest/state，并确保 KB 解析来自 `topics.jsonl`。

步骤：
1. 调用 tool `battle_create_run`，传入 `rulebooks=$1`、`rolesets=$2`。
2. 如需单独重建 manifest，可调用 tool `kb_manifest`。
3. manifest 的解析必须来自 `boom-boom-81/kb/index/topics.jsonl`，不可全库扫描。

说明：
- 默认用户体验应在 OpenCode 命令 + tools 内完成；CLI 只是工具内部的桥接执行体。
