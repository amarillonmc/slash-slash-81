# slash-slash-81

第二阶段 MVP-2：在 wrapper repo 内打通“新建 run → 自动推进回合 → 增强校验 → state extraction / completion → 对局问答”的本地文件工作流。

## 目录结构

- `app/core/`: 索引解析、状态存储、数据结构、校验、state extraction、completion
- `app/cli/`: CLI 入口（`create_run` / `generate_round` / `validate_round` / `next_round` / `ask_record`）
- `app/schemas/`: manifest/state/validation/completion JSON Schema
- `.opencode/commands/`: `/new-battle` `/next-round` `/ask-record` 命令模板（**command-first 主路径**）
- `runs/<run_id>/`: 每次对局的 manifest/state/rounds/qa

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

> 当前实现仅依赖 Python 标准库。

## 推荐工作流（command-first）

```bash
python -m app.cli.create_run --rulebooks "规则书A" --rolesets "角色甲"
python -m app.cli.next_round --run-id <run_id>
python -m app.cli.ask_record --run-id <run_id> --question "本局当前发生了什么？"
```

### 为什么改成 command-first

当前仓库未提供可验证的 OpenCode custom tool 注册配置，且已有实际报错 `TypeError: def.execute is not a function`。因此本次将关键链路明确改为 **CLI + 文件桥接**：

- `/next-round` 直接调用 `python -m app.cli.next_round`
- `/ask-record` 直接调用 `python -m app.cli.ask_record`
- `/new-battle` 直接调用 `python -m app.cli.create_run`

这意味着：即使 custom tools 在某些 OpenCode / Windows 环境不可用，主流程也不会落入“表面成功、实际半失败”的状态。

## 一条命令推进下一回合（核心）

```bash
python -m app.cli.next_round --run-id <run_id>
```

该命令自动执行：
1. 读取 `manifest.json`、`state.json`、resolved KB 文件与历史 final rounds。
2. 生成 `rounds/{n}_draft.md`。
3. 执行增强 validation，写入 `rounds/{n}_validation.json`。
4. 若 validation 通过，则登记 `rounds/{n}_final.md`。
5. finalize 后立刻运行 state extraction / completion，更新 `state.json`。
6. 若 `state.status=completed`，后续再次调用会直接拒绝推进。

## draft / final 的最终语义

本仓库采用**方案 1**：

- `draft` = 完整生成文本，但尚未通过校验、尚未登记 state。
- `final` = 通过校验并完成 state 更新后的正式版本。

在当前实现里，`final` 的正文通常与 `draft` 相同；二者的差异主要在于**生命周期语义**而不是“文本大改写”。如果后续需要，可在 finalize step 增加轻量规范化，但这不是当前前提。

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
  - 非空
  - 回合标题匹配
- `continuity.*`
  - 是否承接上一回合 / 已知状态
  - 是否引用未来回合
- `roles.*`
  - 是否提及关键参与角色
  - 是否把已淘汰角色写成正常行动角色
- `references.*`
  - 是否记录了 rulebooks / roles 校验依据
- `narrative.*`
  - 文本是否过短
  - 是否残留 placeholder / prompt leakage

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

当前提取方式是**启发式文本抽取**，会优先写入可确认事实；对无法确定的状态，会进入 `uncertain_facts` / `unresolved_threads`，而不是伪造确定结论。

完成判定也在这一阶段执行，并落盘到 `state.completion`。若 `completion.is_complete=true`，则 `state.status=completed`。

## CLI 使用

### 1) 新建 run

```bash
python -m app.cli.create_run --rulebooks "规则书A,规则书B" --rolesets "角色甲,角色乙"
```

### 2) 自动推进下一回合（推荐）

```bash
python -m app.cli.next_round --run-id <run_id>
```

### 3) 拆分模式（调试）

```bash
python -m app.cli.generate_round --run-id <run_id>
python -m app.cli.validate_round --run-id <run_id> --round-no <n> --draft runs/<run_id>/rounds/<n>_draft.md --finalize
```

### 4) 对当前 run 提问并记录

```bash
python -m app.cli.ask_record --run-id <run_id> --question "本局当前发生了什么？"
```

## OpenCode 命令

- `/new-battle <rulebooks_csv> <rolesets_csv>`
- `/next-round <run_id>`
- `/ask-record <run_id> <question>`

这些命令现在都以 `.opencode/commands/*.md` 中描述的 CLI 主链路为准，不再假设 custom tools 已可靠接通。

## 本地 smoke-check（建议）

```bash
python -m py_compile app/core/*.py app/cli/*.py
python -m app.cli.validate_round --run-id <run_id> --round-no <n> --draft runs/<run_id>/rounds/<n>_draft.md
python -m app.cli.ask_record --run-id <run_id> --question "谁目前占优，是否已接近终局？"
```

## 已知限制

1. 若 `boom-boom-81/kb/index/topics.jsonl` 不存在（例如 submodule 未拉取），创建 run 会失败。
2. 由于当前仓库中没有可确认兼容的 OpenCode custom tool 注册配置，本次选择了 command-first 主架构，而不是声称“tools 已修通”。
3. state extraction 与 completion 仍是启发式 MVP-2，不等于规则级严谨裁定；复杂规则书仍需继续细化。
4. 当前生成文本本身仍偏模板化，但 validation、state extraction 和 ask-record 已不再只看空壳字段。

## 后续最合理的下一步

- 把 `generate_round` 从模板叙事升级为“基于 state_facts / unresolved_threads 的约束生成”，这样 validation 与 extraction 就能开始对更真实的战局推进做闭环回归测试。
