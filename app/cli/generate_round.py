from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from app.core.kb_index import read_topic_markdown
from app.core.schemas import utc_now_iso
from app.core.state_store import read_json


def _snippet(text: str, max_lines: int = 8) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:max_lines])


def _build_context(manifest: dict) -> List[str]:
    snippets: List[str] = []
    for item in manifest.get("resolved_files", []):
        path = item.get("source_path")
        title = item.get("title")
        if not path:
            continue
        body = read_topic_markdown(path)
        snippets.append(f"## {title}\n{_snippet(body)}")
    return snippets


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate draft content for next round.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", help="optional output markdown path")
    args = parser.parse_args()

    run_dir = Path("runs") / args.run_id
    manifest = read_json(run_dir / "manifest.json")
    state = read_json(run_dir / "state.json")

    # Required by project conventions: always read state before generation.
    current_round = int(state.get("current_round", 0))
    round_no = current_round + 1

    context_snippets = _build_context(manifest)
    alive_roles = state.get("alive_roles", [])
    round_title = f"# Round {round_no} Draft"

    body = [
        round_title,
        "",
        f"- run_id: {args.run_id}",
        f"- generated_at: {utc_now_iso()}",
        f"- alive_roles: {', '.join(alive_roles) if alive_roles else '(none)'}",
        "",
        "## Director Notes",
        "根据规则和角色背景推进本回合叙事，并在最终版中补全细节。",
        "",
        "## Context Snapshots",
        *context_snippets,
        "",
        "## Draft Narrative",
        f"Round {round_no} begins. (OpenCode should rewrite this section into a full narrative.)",
    ]

    output = Path(args.output) if args.output else run_dir / "rounds" / f"{round_no}_draft.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")

    print(json.dumps({"ok": True, "round_no": round_no, "draft": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
