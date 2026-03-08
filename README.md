# slash-slash-81

第二阶段 MVP：在 wrapper repo 内打通“新建 run → 自动推进回合（无需手动改 draft）→ 自动完成判定 → 对局问答”的本地文件工作流。

## 目录结构

- `app/core/`: 索引解析、状态存储、数据结构、校验与完结判定逻辑
- `app/cli/`: CLI 入口（`create_run` / `generate_round` / `validate_round` / `next_round` / `ask_record`）
- `app/prompts/`: 导演、校验、问答 system prompt
- `app/schemas/`: manifest/state/validation/completion JSON Schema
- `.opencode/commands/`: `/new-battle` `/next-round` `/ask-record` 命令模板
- `.opencode/tools/`: OpenCode custom tools（TypeScript wrappers）
- `runs/<run_id>/`: 每次对局的 manifest/state/rounds/qa

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

> 当前实现仅依赖 Python 标准库。

## 一条命令推进下一回合（核心）

```bash
python -m app.cli.next_round --run-id <run_id>
```

该命令自动执行：
1. 读取 `manifest.json`、`state.json`、resolved KB 文件与历史 final rounds。
2. 生成完整可校验的 `rounds/{n}_draft.md`（非占位骨架）。
3. 自动校验并 finalize（写入 `rounds/{n}_final.md`）。
4. 自动做完成判定，必要时将 `state.status` 改为 `completed`。

如果 run 已完成，后续再调用会直接报错拒绝继续推进。

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

`/next-round` 已改为调用闭环工具 `battle_next_round`，不再要求用户手动编辑 draft 或追加提示。

## 完成判定机制（初版）

在 finalize 后执行混合判定：
- 启发式信号：`乱斗结束`、`剧终`、`胜负已定`、`任务完成`、`故事到此结束`、`最终回`、`the end`。
- 结合规则上下文（manifest rulebooks）与文本证据（赢家线索、连续终局信号）进行可信度收敛。

输出写入 `state.completion`：
- `is_complete`
- `reason`
- `signals`
- `winner_like_entities`
- `summary`

当 `is_complete=true` 时：
- `state.status = "completed"`
- `/next-round` 将拒绝继续推进。

## 本地 smoke-check（建议）

```bash
python -m py_compile app/core/*.py app/cli/*.py
python -m app.cli.create_run --rulebooks "规则书A" --rolesets "角色甲" --run-id demo2
python -m app.cli.next_round --run-id demo2
python -m app.cli.next_round --run-id demo2
python -m app.cli.ask_record --run-id demo2 --question "谁目前占优，是否已接近终局？"
```

## 已知限制

1. 若 `boom-boom-81/kb/index/topics.jsonl` 不存在（例如 submodule 未拉取），创建 run 会失败。
2. 本阶段生成文本仍是模板化自动叙事，已无需人工补稿；后续可在不改变闭环流程的前提下接入更强模型生成。
3. 完成判定为初版混合策略，复杂规则书的终局逻辑可继续细化。

## 后续最合理的下一步

- 在 `state` 中增加更结构化的角色状态迁移（伤亡、阵营目标、任务进度），并将完成判定从“信号+证据”升级到“规则子句可追溯”级别。
