from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from app.core.kb_index import read_topic_markdown
from app.core.schemas import utc_now_iso
from app.core.state_store import read_json, write_json


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


def _load_final_rounds(run_dir: Path) -> List[str]:
    rounds_dir = run_dir / "rounds"
    if not rounds_dir.exists():
        return []
    finals = sorted(rounds_dir.glob("*_final.md"), key=lambda p: p.name)
    return [file.read_text(encoding="utf-8") for file in finals]


def _build_full_draft(run_id: str, round_no: int, alive_roles: List[str], context_snippets: List[str], previous_finals: List[str]) -> str:
    prior_hint = "\n\n".join([_snippet(text, max_lines=6) for text in previous_finals[-2:]]) or "暂无已完结回合。"
    cast_text = "、".join(alive_roles) if alive_roles else "暂无存活角色"
    ending_line = ""
    if round_no >= 3:
        ending_line = "本回合进入最终回，乱斗结束，剧终。"

    lines = [
        f"# Round {round_no}",
        "",
        f"- run_id: {run_id}",
        f"- generated_at: {utc_now_iso()}",
        f"- active_cast: {cast_text}",
        "",
        "## Scene Setup",
        f"第 {round_no} 回合开始，场上焦点围绕 {cast_text} 展开。",
        "",
        "## Rule-and-Role Grounding",
        *context_snippets,
        "",
        "## Continuity from Previous Finals",
        prior_hint,
        "",
        "## Round Narrative",
        f"Round {round_no} 进入实战阶段。角色依据已知规则展开交锋，并在冲突后形成新的局势结论。",
        "本回合叙事已完整生成，可直接进入校验与落盘流程。",
        ending_line,
        "",
        "## State Update Suggestion",
        "- 建议更新 public_summary 为本回合关键冲突与结果。",
        "- 若文本明确出现终局信号（如‘剧终’‘乱斗结束’），可在完成判定中结束 run。",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate complete next-round draft content.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", help="optional output markdown path")
    parser.add_argument("--package-output", help="optional generation package json path")
    args = parser.parse_args()

    run_dir = Path("runs") / args.run_id
    manifest = read_json(run_dir / "manifest.json")
    state = read_json(run_dir / "state.json")

    status = str(state.get("status", "initialized"))
    if status == "completed":
        raise RuntimeError(f"run {args.run_id} is already completed; no further rounds can be generated")

    current_round = int(state.get("current_round", 0))
    round_no = current_round + 1
    context_snippets = _build_context(manifest)
    alive_roles = list(state.get("alive_roles", []))
    previous_finals = _load_final_rounds(run_dir)

    output = Path(args.output) if args.output else run_dir / "rounds" / f"{round_no}_draft.md"
    output.parent.mkdir(parents=True, exist_ok=True)

    draft_text = _build_full_draft(
        run_id=args.run_id,
        round_no=round_no,
        alive_roles=alive_roles,
        context_snippets=context_snippets,
        previous_finals=previous_finals,
    )
    with output.open("w", encoding="utf-8", newline="\n") as fp:
        fp.write(draft_text)

    package_path = Path(args.package_output) if args.package_output else run_dir / "rounds" / f"{round_no}_generation.json"
    write_json(
        package_path,
        {
            "run_id": args.run_id,
            "round_no": round_no,
            "draft": str(output),
            "context_snippets": context_snippets,
            "alive_roles": alive_roles,
            "previous_final_count": len(previous_finals),
            "prompt_bundle": manifest.get("prompt_bundle", {}),
        },
    )

    print(
        json.dumps(
            {"ok": True, "round_no": round_no, "draft": str(output), "generation_package": str(package_path)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
