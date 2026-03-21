from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from app.core.completion import assess_completion
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate round draft and optionally promote to final.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--round-no", required=True, type=int)
    parser.add_argument("--draft", required=True, help="draft markdown path")
    parser.add_argument("--report", help="validation report output path")
    parser.add_argument("--finalize", action="store_true", help="copy draft to final and update state on success")
    args = parser.parse_args()

    run_dir = Path("runs") / args.run_id
    state_path = run_dir / "state.json"
    manifest_path = run_dir / "manifest.json"
    state_data = read_json(state_path)
    manifest_data = read_json(manifest_path)
    round_text = Path(args.draft).read_text(encoding="utf-8")

    if str(state_data.get("status", "")) == "completed":
        raise RuntimeError(f"run {args.run_id} is already completed; refusing to validate new round")

    report = validate_round_text(round_text=round_text, alive_roles=state_data.get("alive_roles", []), expected_round=args.round_no)
    report_path = Path(args.report) if args.report else run_dir / "rounds" / f"{args.round_no}_validation.json"
    write_json(report_path, report.to_dict())

    final_path = run_dir / "rounds" / f"{args.round_no}_final.md"
    completion_report = None
    if args.finalize and report.ok:
        with final_path.open("w", encoding="utf-8", newline="\n") as fp:
            fp.write(round_text)

        previous_finals = _load_previous_finals(run_dir, args.round_no)
        rulebooks = list(manifest_data.get("rulebooks", []))
        roles = list(manifest_data.get("roles", []))
        completion_report = assess_completion(
            round_text=round_text,
            previous_finals=previous_finals,
            rulebook_titles=rulebooks,
            roles=roles,
            state_status=str(state_data.get("status", "initialized")),
        )

        history = list(state_data.get("round_history", []))
        history_item = RoundHistoryItem(
            round_no=args.round_no,
            draft_file=f"rounds/{args.round_no}_draft.md",
            final_file=f"rounds/{args.round_no}_final.md",
            validation_file=f"rounds/{args.round_no}_validation.json",
            summary=f"Round {args.round_no} finalized.",
        )
        history.append(asdict(history_item))

        new_status = "completed" if completion_report.get("is_complete") else "in_progress"
        new_summary = completion_report.get("summary") if completion_report else f"Round {args.round_no} completed."

        new_state = State(
            run_id=args.run_id,
            current_round=args.round_no,
            status=new_status,
            alive_roles=list(state_data.get("alive_roles", [])),
            eliminated_roles=list(state_data.get("eliminated_roles", [])),
            round_history=history,
            public_summary=str(new_summary),
            private_notes=str(state_data.get("private_notes", "")),
            updated_at=utc_now_iso(),
            completion=completion_report,
        )
        write_json(state_path, new_state.to_dict())

    print(
        json.dumps(
            {
                "ok": report.ok,
                "report": str(report_path),
                "final": str(final_path) if args.finalize and report.ok else None,
                "completion": completion_report,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
