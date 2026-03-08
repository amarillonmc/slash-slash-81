from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from app.core.kb_index import read_topic_markdown
from app.core.state_store import read_json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _collect_round_finals(run_dir: Path) -> List[Tuple[str, str]]:
    rounds_dir = run_dir / "rounds"
    if not rounds_dir.exists():
        return []
    files = sorted(rounds_dir.glob("*_final.md"), key=lambda p: p.name)
    return [(file.name, file.read_text(encoding="utf-8")) for file in files]


def _tokenize(text: str) -> List[str]:
    return [token for token in re.split(r"[^\w\u4e00-\u9fff]+", text.lower()) if token]


def _score(text: str, query_tokens: List[str]) -> int:
    lowered = text.lower()
    return sum(1 for token in query_tokens if token and token in lowered)


def _pick_kb_context(question: str, manifest: Dict[str, object]) -> List[str]:
    question_tokens = _tokenize(question)
    snippets: List[str] = []

    for item in manifest.get("resolved_files", []):
        if item.get("category") not in {"rulebooks", "roles", "records"}:
            continue
        body = read_topic_markdown(item.get("source_path", ""))
        title = str(item.get("title", ""))
        score = _score(body, question_tokens)
        if score <= 0:
            continue
        summary_lines = [line.strip() for line in body.splitlines() if line.strip()][:5]
        snippets.append(f"[{item.get('category')}] {title}: {' / '.join(summary_lines)}")

    return snippets[:4]


def _build_answer(question: str, state: Dict[str, object], finals: List[Tuple[str, str]], kb_context: List[str]) -> str:
    tokens = _tokenize(question)
    ranked_rounds = sorted(finals, key=lambda item: _score(item[1], tokens), reverse=True)
    top_rounds = [item for item in ranked_rounds if _score(item[1], tokens) > 0][:2] or ranked_rounds[-2:]

    round_evidence = []
    for name, content in top_rounds:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        round_evidence.append(f"- {name}: {' '.join(lines[:2])}")

    completion = state.get("completion") or {}
    completion_line = "已完结" if state.get("status") == "completed" else "进行中"
    if isinstance(completion, dict) and completion.get("reason"):
        completion_line += f"（{completion.get('reason')}）"

    kb_lines = "\n".join([f"- {item}" for item in kb_context]) if kb_context else "- 无明显匹配的 KB 片段"
    rounds_text = "\n".join(round_evidence) if round_evidence else "- 暂无 final rounds"

    return (
        f"问题：{question}\n\n"
        f"结论：基于当前 run 记录，状态为 {completion_line}，当前回合 {state.get('current_round', 0)}。\n\n"
        f"回合证据：\n{rounds_text}\n\n"
        f"规则/角色/记录证据：\n{kb_lines}\n\n"
        "说明：本回答由本地 MVP 检索与汇总生成，可继续扩展为更强的模型问答。"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Answer a question using run record and KB files.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--question", required=True)
    args = parser.parse_args()

    run_dir = Path("runs") / args.run_id
    manifest = read_json(run_dir / "manifest.json")
    state = read_json(run_dir / "state.json")
    finals = _collect_round_finals(run_dir)

    kb_context = _pick_kb_context(args.question, manifest)
    answer = _build_answer(args.question, state, finals, kb_context)

    qa_path = run_dir / "qa" / "qa.jsonl"
    qa_item = {
        "ts": utc_now_iso(),
        "question": args.question,
        "answer": answer,
        "evidence_count": {"final_rounds": len(finals), "kb_snippets": len(kb_context)},
    }
    with qa_path.open("a", encoding="utf-8", newline="\n") as fp:
        fp.write(json.dumps(qa_item, ensure_ascii=False) + "\n")

    print(json.dumps({"ok": True, "answer": answer, "qa_file": str(qa_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
