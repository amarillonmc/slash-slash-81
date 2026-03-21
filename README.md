# slash-slash-81

第二阶段 MVP-2：在 wrapper repo 内打通“新建 run → OpenCode 内自动推进回合 → 增强校验 → state extraction / completion → 对局问答”的本地文件工作流。

## 目录结构

- `app/core/`: 索引解析、状态存储、数据结构、校验、state extraction、completion
- `app/cli/`: CLI 入口（`create_run` / `generate_round` / `validate_round` / `next_round` / `ask_record`）
- `app/schemas/`: manifest/state/validation/completion JSON Schema
- `.opencode/tools/`: OpenCode custom tools（主路径，内部桥接 Python CLI）
- `.opencode/commands/`: `/new-battle` `/next-round` `/ask-record` 命令模板
- `opencode.json`: 项目级 OpenCode 配置与 tool permissions
- `runs/<run_id>/`: 每次对局的 manifest/state/rounds/qa

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

> 当前核心业务逻辑仍只依赖 Python 标准库；OpenCode tool 定义文件使用 `zod`/OpenCode runtime，在 OpenCode 环境中加载。

## OpenCode 主工作流

默认是在 OpenCode 中使用以下命令：

- `/new-battle <rulebooks_csv> <rolesets_csv>`
- `/next-round <run_id>`
- `/ask-record <run_id> <question>`

本次修复后，custom tools 已恢复为 **OpenCode 主路径**：

- `run_state`：读取 `runs/<run_id>/state.json`
- `kb_manifest`：构建 manifest
- `battle_generate`：生成 draft
- `battle_validate`：校验 / finalize
- `battle_next_round`：执行完整 next-round 闭环

这些 tools 现在使用符合当前 OpenCode custom tools 文档的导出结构：`description` + `args` + `execute(...)`，不再是旧版“默认导出 async function”那种会触发 `def.execute is not a function` 的形式。OpenCode 项目配置也已补上 `opencode.json`。 

## 一条命令推进下一回合（核心）

在 OpenCode 中推荐直接运行：

```text
/next-round <run_id>
```

其逻辑为：
1. 先通过 `run_state` 读取 `runs/<run_id>/state.json`。
2. 若 run 已 completed，则立即拒绝继续推进。
3. 否则调用 `battle_next_round`。
4. `battle_next_round` 内部再执行 Python CLI，完成：
   - 读取 `manifest.json`、`state.json`、resolved KB 文件与历史 final rounds
   - 生成 `rounds/{n}_draft.md`
   - 执行增强 validation，写入 `rounds/{n}_validation.json`
   - 若通过则落盘 `rounds/{n}_final.md`
   - finalize 后立刻运行 state extraction / completion，更新 `state.json`

因此，OpenCode 侧负责多 agent / LLM / tool 调度，本仓库的 Python CLI 则负责稳定的本地文件落盘与规则化状态迁移。

## draft / final 的最终语义

本仓库采用**方案 1**：

- `draft` = 完整生成文本，但尚未通过校验、尚未登记 state。
- `final` = 通过校验并完成 state 更新后的正式版本。

在当前实现里，`final` 的正文通常与 `draft` 相同；差异主要在于生命周期语义，而不是必须大改文本。

## Validation（增强版）

`validation.json` 现在至少包含：

- `ok`
- `errors`
- `warnings`
- `checks`
- `sources_considered`
- `summary`

当前已实现的检查分组包括：

- `structure.*`
- `continuity.*`
- `roles.*`
- `references.*`
- `narrative.*`

即使某些检查仍是启发式，report 也会保留 warning，而不是无条件判通过。

## State extraction / completion

在 finalize 后，系统会从 `final.md` 和既有 state 中提取并更新：

- `public_summary`
- `private_notes`
- `alive_roles`
- `eliminated_roles`
- `phase`
- `state_facts`
- `notable_events`
- `unresolved_threads`
- `uncertain_facts`
- `extraction`
- `completion`

当前提取方式是启发式文本抽取，会优先写入可确认事实；无法确定的状态会进入 `uncertain_facts` / `unresolved_threads`。

## CLI（底层调试路径）

若需要绕过 OpenCode 命令做调试，可直接执行：

```bash
python -m app.cli.create_run --rulebooks "规则书A,规则书B" --rolesets "角色甲,角色乙"
python -m app.cli.next_round --run-id <run_id>
python -m app.cli.ask_record --run-id <run_id> --question "本局当前发生了什么？"
```

这些 CLI 仍是 tool 的底层执行体，但默认用户路径应是 OpenCode 命令 + tools。

## 本地 smoke-check（建议）

```bash
python -m py_compile app/core/*.py app/cli/*.py
python -m app.cli.validate_round --run-id <run_id> --round-no <n> --draft runs/<run_id>/rounds/<n>_draft.md
python -m app.cli.ask_record --run-id <run_id> --question "谁目前占优，是否已接近终局？"
```

## 已知限制

1. 若 `boom-boom-81/kb/index/topics.jsonl` 不存在（例如 submodule 未拉取），创建 run 会失败。
2. 当前环境中未安装 OpenCode 可执行文件，因此仓库内无法直接做 end-to-end 的 OpenCode 运行验证；本次修复基于当前官方 custom-tools / config 文档完成兼容改造。
3. state extraction 与 completion 仍是启发式 MVP-2，不等于规则级严谨裁定；复杂规则书仍需继续细化。
4. 当前生成文本本身仍偏模板化，但 validation、state extraction 和 ask-record 已不再只看空壳字段。

## 后续最合理的下一步

- 为 `.opencode/tools/*.js` 增加一个最小的本地加载检查脚本（mock `zod`/runtime），以便在没有 OpenCode 二进制的 CI 环境中也能尽量验证 tool definition 结构。
