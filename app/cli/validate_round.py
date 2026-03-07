from __future__ import annotations

import argparse
import json
from pathlib import Path

from dataclasses import asdict

from app.core.schemas import RoundHistoryItem, State, utc_now_iso
from app.core.state_store import read_json, write_json
from app.core.validation import validate_round_text


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
    state_data = read_json(state_path)
    round_text = Path(args.draft).read_text(encoding="utf-8")

    report = validate_round_text(round_text=round_text, alive_roles=state_data.get("alive_roles", []), expected_round=args.round_no)
    report_path = Path(args.report) if args.report else run_dir / "rounds" / f"{args.round_no}_validation.json"
    write_json(report_path, report.to_dict())

    final_path = run_dir / "rounds" / f"{args.round_no}_final.md"
    if args.finalize and report.ok:
        final_path.write_text(round_text, encoding="utf-8", newline="\n")

        history = list(state_data.get("round_history", []))
        history_item = RoundHistoryItem(
                round_no=args.round_no,
                draft_file=f"rounds/{args.round_no}_draft.md",
                final_file=f"rounds/{args.round_no}_final.md",
                validation_file=f"rounds/{args.round_no}_validation.json",
                summary=f"Round {args.round_no} finalized.",
            )
        history.append(asdict(history_item))
        new_state = State(
            run_id=args.run_id,
            current_round=args.round_no,
            status="in_progress",
            alive_roles=list(state_data.get("alive_roles", [])),
            eliminated_roles=list(state_data.get("eliminated_roles", [])),
            round_history=history,
            public_summary=f"Round {args.round_no} completed.",
            private_notes=str(state_data.get("private_notes", "")),
            updated_at=utc_now_iso(),
        )
        write_json(state_path, new_state.to_dict())

    print(
        json.dumps(
            {
                "ok": report.ok,
                "report": str(report_path),
                "final": str(final_path) if args.finalize and report.ok else None,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
