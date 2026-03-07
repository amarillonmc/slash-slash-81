from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from app.core.kb_index import read_topic_markdown
from app.core.state_store import read_json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _collect_round_finals(run_dir: Path) -> List[str]:
    rounds_dir = run_dir / "rounds"
    if not rounds_dir.exists():
        return []
    files = sorted(rounds_dir.glob("*_final.md"), key=lambda p: p.name)
    return [file.read_text(encoding="utf-8") for file in files]


def main() -> None:
    parser = argparse.ArgumentParser(description="Answer a question using run record and KB files.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--question", required=True)
    args = parser.parse_args()

    run_dir = Path("runs") / args.run_id
    manifest = read_json(run_dir / "manifest.json")
    state = read_json(run_dir / "state.json")

    round_texts = _collect_round_finals(run_dir)
    kb_titles = []
    for item in manifest.get("resolved_files", []):
        if item.get("category") in {"rulebooks", "roles"}:
            kb_titles.append(item.get("title", ""))

    summary = state.get("public_summary", "")
    answer = (
        f"问题：{args.question}\n"
        f"当前回合：{state.get('current_round', 0)}\n"
        f"状态摘要：{summary}\n"
        f"已加载规则/角色：{', '.join([x for x in kb_titles if x])}\n"
        f"已完成回合数：{len(round_texts)}\n"
        "说明：当前为 MVP 规则检索回答，后续可替换成模型增强问答。"
    )

    for item in manifest.get("resolved_files", []):
        if item.get("category") == "records":
            _ = read_topic_markdown(item.get("source_path", ""))

    qa_path = run_dir / "qa" / "qa.jsonl"
    qa_item = {
        "ts": utc_now_iso(),
        "question": args.question,
        "answer": answer,
    }
    with qa_path.open("a", encoding="utf-8", newline="\n") as fp:
        fp.write(json.dumps(qa_item, ensure_ascii=False) + "\n")

    print(json.dumps({"ok": True, "answer": answer, "qa_file": str(qa_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
