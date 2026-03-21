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


def _pick_kb_context(question: str, manifest: Dict[str, object]) -> List[Dict[str, str]]:
    question_tokens = _tokenize(question)
    snippets: List[Dict[str, str]] = []

    for item in manifest.get("resolved_files", []):
        if item.get("category") not in {"rulebooks", "roles", "records"}:
            continue
        try:
            body = read_topic_markdown(item.get("source_path", ""))
        except RuntimeError:
            continue
        title = str(item.get("title", ""))
        score = _score(body, question_tokens)
        if score <= 0:
            continue
        summary_lines = [line.strip() for line in body.splitlines() if line.strip()][:5]
        snippets.append(
            {
                "category": str(item.get("category")),
                "title": title,
                "path": str(item.get("source_path", "")),
                "snippet": " / ".join(summary_lines),
            }
        )

    return snippets[:4]


def _build_answer(question: str, state: Dict[str, object], finals: List[Tuple[str, str]], kb_context: List[Dict[str, str]]) -> Tuple[str, List[str]]:
    tokens = _tokenize(question)
    ranked_rounds = sorted(finals, key=lambda item: _score(item[1], tokens), reverse=True)
    top_rounds = [item for item in ranked_rounds if _score(item[1], tokens) > 0][:3]
    if not top_rounds:
        top_rounds = finals[-3:]

    evidence_refs: List[str] = []
    round_evidence = []
    for name, content in top_rounds:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        summary = " ".join(lines[:3])[:220]
        round_evidence.append(f"- {name}: {summary}")
        evidence_refs.append(f"final:{name}")

    completion = state.get("completion") or {}
    completion_line = "已完结" if state.get("status") == "completed" else "进行中"
    if isinstance(completion, dict) and completion.get("reason"):
        completion_line += f"（{completion.get('reason')}）"

    state_lines = [
        f"- 当前回合：{state.get('current_round', 0)}",
        f"- phase：{state.get('phase', 'unknown')}",
        f"- public_summary：{state.get('public_summary', '')}",
        f"- 存活角色：{'、'.join(state.get('alive_roles', [])) or '未知'}",
        f"- 已淘汰角色：{'、'.join(state.get('eliminated_roles', [])) or '暂无明确记录'}",
    ]
    if state.get("notable_events"):
        state_lines.append(f"- notable_events：{'；'.join(state.get('notable_events', [])[:3])}")
    if state.get("unresolved_threads"):
        state_lines.append(f"- unresolved：{'；'.join(state.get('unresolved_threads', [])[:2])}")

    kb_lines = []
    for item in kb_context:
        kb_lines.append(f"- [{item['category']}] {item['title']}: {item['snippet']}")
        evidence_refs.append(f"kb:{item['title']}")

    uncertainty_line = ""
    if not top_rounds:
        uncertainty_line = "\n不确定性：当前 run 尚无 final round，回答只能基于 state 和 manifest。"
    elif tokens and all(_score(content, tokens) == 0 for _, content in finals):
        uncertainty_line = "\n不确定性：问题与现有 round 记录的直接匹配度较低，以下回答偏向摘要而非精确裁定。"

    answer = (
        f"问题：{question}\n\n"
        f"结论：基于当前 run 记录，状态为 {completion_line}。\n\n"
        f"状态摘要：\n" + "\n".join(state_lines) + "\n\n"
        f"回合证据：\n" + ("\n".join(round_evidence) if round_evidence else "- 暂无 final rounds") + "\n\n"
        f"规则/角色证据：\n" + ("\n".join(kb_lines) if kb_lines else "- 当前问题未命中明显相关的 rulebooks / roles 片段") +
        f"{uncertainty_line}\n\n说明：若记录中没有明确写出某项事实，本回答会保留不确定。"
    )
    return answer, evidence_refs


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
    answer, evidence_refs = _build_answer(args.question, state, finals, kb_context)

    qa_path = run_dir / "qa" / "qa.jsonl"
    qa_item = {
        "ts": utc_now_iso(),
        "question": args.question,
        "answer": answer,
        "evidence": evidence_refs,
        "evidence_count": {"final_rounds": len(finals), "kb_snippets": len(kb_context)},
        "run_status": state.get("status"),
        "completion": state.get("completion"),
    }
    with qa_path.open("a", encoding="utf-8", newline="\n") as fp:
        fp.write(json.dumps(qa_item, ensure_ascii=False) + "\n")

    print(json.dumps({"ok": True, "answer": answer, "qa_file": str(qa_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
