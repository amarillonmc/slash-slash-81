# slash-slash-81

第一阶段 MVP：在 wrapper repo 内打通“新建 run → 生成下一回合 → 记录问答”的本地文件工作流。

## 目录结构

- `app/core/`: 索引解析、状态存储、数据结构、校验逻辑
- `app/cli/`: CLI 入口（create_run / generate_round / validate_round / ask_record）
- `app/prompts/`: 导演、校验、问答 system prompt
- `app/schemas/`: manifest/state/validation 的 JSON Schema
- `.opencode/commands/`: `/new-battle` `/next-round` `/ask-record` 命令模板
- `.opencode/tools/`: OpenCode custom tools（TypeScript wrappers）
- `runs/<run_id>/`: 每次对局的 manifest/state/rounds/qa

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

> 当前 MVP 仅依赖 Python 标准库。

## CLI 使用

### 1) 新建 run

```bash
python -m app.cli.create_run --rulebooks "规则书A,规则书B" --rolesets "角色甲,角色乙"
```

### 2) 生成下一回合 draft

```bash
python -m app.cli.generate_round --run-id <run_id>
```

### 3) 校验并落盘 final（通过才更新 state）

```bash
python -m app.cli.validate_round --run-id <run_id> --round-no 1 --draft runs/<run_id>/rounds/1_draft.md --finalize
```

### 4) 对当前 run 提问并记录

```bash
python -m app.cli.ask_record --run-id <run_id> --question "本局当前发生了什么？"
```

## OpenCode 命令

- `/new-battle <rulebooks_csv> <rolesets_csv>`
- `/next-round <run_id>`
- `/ask-record <run_id> <question>`

命令定义在 `.opencode/commands/*.md`，工具定义在 `.opencode/tools/*.ts`。

## 本地 smoke-check（建议顺序）

```bash
python -m py_compile app/core/*.py app/cli/*.py
python -m app.cli.create_run --rulebooks "规则书A" --rolesets "角色甲"
python -m app.cli.generate_round --run-id <run_id>
python -m app.cli.validate_round --run-id <run_id> --round-no 1 --draft runs/<run_id>/rounds/1_draft.md --finalize
python -m app.cli.ask_record --run-id <run_id> --question "请总结当前状态"
```

## 已知限制

1. 当前仓库中的 `boom-boom-81/` 若为空（submodule 未拉取），`topics.jsonl` 无法解析，创建 run 会失败。
2. `/next-round` 的“叙事生成”目前是 MVP 草稿模板 + 命令模板约束，尚未内置真实复杂规则演算。
3. `ask_record` 是轻量问答实现，后续可替换成更强的模型检索/推理流程。

## 后续最合理的下一步

- 在保持文件结构不变的前提下，补充“角色淘汰/胜负判定/违规细则”等规则校验器，并接入更精细的 round state 变更逻辑。
