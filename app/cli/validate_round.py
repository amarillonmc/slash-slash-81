from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from app.core.extraction import extract_state_update
from app.core.schemas import RoundHistoryItem, State, utc_now_iso
from app.core.state_store import read_json, write_json
from app.core.validation import validate_round_text


def _load_previous_finals(run_dir: Path, current_round: int) -> List[str]:
    finals: List[str] = []
    rounds_dir = run_dir / "rounds"
    if not rounds_dir.exists():
        return finals
    for file in sorted(rounds_dir.glob("*_final.md"), key=lambda p: p.name):
        if file.name == f"{current_round}_final.md":
            continue
        finals.append(file.read_text(encoding="utf-8"))
    return finals


def _manifest_sources(manifest_data: dict) -> List[str]:
    sources: List[str] = []
    for item in manifest_data.get("resolved_files", []):
        category = str(item.get("category", "unknown"))
        title = str(item.get("title", ""))
        path = str(item.get("source_path", ""))
        sources.append(f"{category}:{title}:{path}")
    return sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate round draft and optionally promote to final.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--round-no", required=True, type=int)
    parser.add_argument("--draft", required=True, help="draft markdown path")
    parser.add_argument("--report", help="validation report output path")
    parser.add_argument("--finalize", action="store_true", help="promote draft to final and update state on success")
    args = parser.parse_args()

    run_dir = Path("runs") / args.run_id
    state_path = run_dir / "state.json"
    manifest_path = run_dir / "manifest.json"
    state_data = read_json(state_path)
    manifest_data = read_json(manifest_path)
    round_text = Path(args.draft).read_text(encoding="utf-8")

    if str(state_data.get("status", "")) == "completed":
        raise RuntimeError(f"run {args.run_id} is already completed; refusing to validate new round")

    previous_finals = _load_previous_finals(run_dir, args.round_no)
    previous_final = previous_finals[-1] if previous_finals else ""
    report = validate_round_text(
        round_text=round_text,
        alive_roles=list(state_data.get("alive_roles", [])),
        eliminated_roles=list(state_data.get("eliminated_roles", [])),
        expected_round=args.round_no,
        previous_final=previous_final,
        sources_considered=_manifest_sources(manifest_data),
    )
    report_path = Path(args.report) if args.report else run_dir / "rounds" / f"{args.round_no}_validation.json"
    write_json(report_path, report.to_dict())

    final_path = run_dir / "rounds" / f"{args.round_no}_final.md"
    state_update = None
    completion_report = None
    if args.finalize and report.ok:
        with final_path.open("w", encoding="utf-8", newline="\n") as fp:
            fp.write(round_text)

        state_update = extract_state_update(
            round_text=round_text,
            round_no=args.round_no,
            manifest=manifest_data,
            previous_state=state_data,
            previous_final=previous_final,
        )
        completion_report = state_update.get("completion")

        history = list(state_data.get("round_history", []))
        history_item = RoundHistoryItem(
            round_no=args.round_no,
            draft_file=f"rounds/{args.round_no}_draft.md",
            final_file=f"rounds/{args.round_no}_final.md",
            validation_file=f"rounds/{args.round_no}_validation.json",
            summary=str(state_update.get("public_summary", f"Round {args.round_no} finalized.")),
        )
        history.append(asdict(history_item))

        new_state = State(
            run_id=args.run_id,
            current_round=int(state_update.get("current_round", args.round_no)),
            status=str(state_update.get("status", "in_progress")),
            alive_roles=list(state_update.get("alive_roles", state_data.get("alive_roles", []))),
            eliminated_roles=list(state_update.get("eliminated_roles", state_data.get("eliminated_roles", []))),
            round_history=history,
            public_summary=str(state_update.get("public_summary", f"Round {args.round_no} completed.")),
            private_notes=str(state_update.get("private_notes", state_data.get("private_notes", ""))),
            updated_at=utc_now_iso(),
            phase=str(state_update.get("phase", state_data.get("phase", "midgame"))),
            state_facts=list(state_update.get("state_facts", state_data.get("state_facts", []))),
            notable_events=list(state_update.get("notable_events", state_data.get("notable_events", []))),
            unresolved_threads=list(state_update.get("unresolved_threads", state_data.get("unresolved_threads", []))),
            uncertain_facts=list(state_update.get("uncertain_facts", state_data.get("uncertain_facts", []))),
            extraction=state_update.get("extraction"),
            completion=completion_report,
        )
        write_json(state_path, new_state.to_dict())

    print(
        json.dumps(
            {
                "ok": report.ok,
                "report": str(report_path),
                "final": str(final_path) if args.finalize and report.ok else None,
                "state_update": state_update,
                "completion": completion_report,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
