# AGENTS.md

Currently, This repository is a wrapper repo with one git submodule.
Most code and docs live in `boom-boom-81/`.

## Additional Information
- 本项目的知识源在 boom-boom-81/kb/
- 回答和生成前先查 boom-boom-81/kb/index/topics.jsonl
- 规则问题只读 rulebooks
- 角色问题只读 roles
- 对局问题优先读 records-completed
- 不允许全库全文扫描
- 每次生成前必须先读取 runs/<run_id>/state.json

## Scope and layout
- Root repo `slash-slash-81/` mainly tracks the submodule pointer.
- Primary implementation lives in `boom-boom-81/tools/`.
- Primary data lives in `boom-boom-81/kb/`.
- Sync script: `boom-boom-81/tools/no81_sync/sync.py`.
- Doc generation scripts: `boom-boom-81/tools/docgen/*.py`.
- MkDocs config: `boom-boom-81/mkdocs.yaml`.

## Environment assumptions
- Python 3.10+ recommended (uses `zoneinfo`, annotations, dataclasses).
- Run commands from `boom-boom-81/` unless noted otherwise.
- Use UTF-8 for all reads/writes.
- Keep line endings normalized to LF for generated text outputs.

## Setup commands
```bash
# from repository root
cd boom-boom-81

# optional but recommended
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# install runtime dependencies
python -m pip install -r tools/no81_sync/requirements.txt
```

## Build / lint / test commands
This project has no formal build system and no configured test suite yet.
Use the commands below as the canonical validation workflow.

### 1) Syntax check (fast, required)
```bash
python -m py_compile tools/no81_sync/sync.py
python -m py_compile tools/docgen/gen_roles_by_author.py
python -m py_compile tools/docgen/gen_roles_by_author_json.py
python -m py_compile tools/docgen/gen_roles_all.py
```

### 2) Dry-run behavior check (safe smoke test)
```bash
python tools/no81_sync/sync.py --dry-run
python tools/no81_sync/sync.py --mode maintenance-local --dry-run
```

### 3) Category-scoped smoke check
```bash
python tools/no81_sync/sync.py --category roles --dry-run
python tools/no81_sync/sync.py --category rulebooks --dry-run
python tools/no81_sync/sync.py --category records --dry-run
```

### 4) Documentation build check (optional)
```bash
mkdocs build
# or explicitly
mkdocs build -f mkdocs.yaml
```

### 5) Generate derived docs/index views
```bash
python tools/docgen/gen_roles_all.py
python tools/docgen/gen_roles_by_author.py
python tools/docgen/gen_roles_by_author_json.py
```

## Running a single test
There is currently no `tests/` directory and no `pytest` config.
If you add pytest tests, use this convention:
```bash
# run one file
python -m pytest tests/test_sync.py

# run one test function
python -m pytest tests/test_sync.py::test_parse_forum_time_to_iso

# run one parameterized case by keyword
python -m pytest tests/test_sync.py -k "yesterday_case"
```
When introducing tests, also add `pytest` to a managed dependency file.

## Config and secrets
- Copy `tools/no81_sync/config.example.env` to `tools/no81_sync/.env`.
- Required keys for full sync:
  - `SMF_BASE_URL`
  - `SMF_USERNAME`
  - `SMF_PASSWORD`
- Optional operational keys include:
  - `REQUEST_DELAY_MS`, `USER_AGENT`
  - `ENABLE_REPORT_POST`, `REPORT_ON_START`, `REPORT_ON_FINISH`, `REPORT_TOPIC_ID`
  - `SKIP_EXISTING_TOPICS`, `AUTHOR_SAMPLE_SIZE`
- Never commit `.env` or `tools/no81_sync/state/`.

## Code style guidelines

### Imports
- Keep imports at module top.
- Group in order: stdlib, third-party, local.
- Prefer explicit imports over wildcard imports.
- Use `from __future__ import annotations` in Python modules (already used).

### Formatting
- Follow PEP 8 defaults.
- Use 4 spaces for indentation.
- Keep function blocks compact and readable; favor small helpers.
- Preserve existing LF newline behavior in generated files.
- Do not reformat unrelated files in broad style-only passes.

### Types
- Use type hints on public and non-trivial helpers.
- Prefer concrete typing used in this repo: `Dict`, `List`, `Optional`, `Tuple`, `Set`.
- Use dataclasses for structured records (`TopicRef`, `TopicResult`, etc.).
- Keep return types explicit for parser/transformer functions.

### Naming conventions
- `snake_case` for functions, variables, and module-level helpers.
- `PascalCase` for dataclasses and classes.
- `UPPER_SNAKE_CASE` for constants.
- Use descriptive names tied to forum/KB domain semantics.

### Error handling
- Fail fast on missing required config or malformed critical inputs.
- Raise `RuntimeError` for operational failures with actionable messages.
- Convert recoverable item-level failures to warnings where possible.
- In batch loops, continue processing after per-topic failures.
- Keep stderr user-facing and concise in CLI entry points.

### I/O and encoding
- Always read/write text with `encoding="utf-8"`.
- Use `ensure_ascii=False` for JSON written from multilingual content.
- Normalize path separators to `/` for stored index paths.
- Keep generated markdown deterministic where practical.

### Markdown/index generation
- Preserve frontmatter key order used by `render_frontmatter`.
- Keep category mapping stable:
  - `roles -> kb/roles`
  - `rulebooks -> kb/rulebooks`
  - `records -> kb/records-completed`
- Treat spoiler-related warnings as data quality signals, not hard crashes.

## Operational conventions for agents
- Prefer `--dry-run` before non-trivial sync changes.
- Prefer category-scoped runs for faster iteration.
- Validate changed Python files with `py_compile` before finishing.
- Avoid editing large generated KB content unless the task requires it.
- Keep changes focused on requested scope; avoid drive-by rewrites.

## Cursor / Copilot rules status
Checked for repository-level instruction files:
- `.cursorrules`: not found
- `.cursor/rules/`: not found
- `.github/copilot-instructions.md`: not found

If any of these files are added later, treat them as higher-priority agent instructions and update this document.
