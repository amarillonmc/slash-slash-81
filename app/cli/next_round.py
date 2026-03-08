from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from app.core.state_store import read_json


def _run_json(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise RuntimeError(message)
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one fully automated next-round cycle.")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    try:
        state = read_json(Path("runs") / args.run_id / "state.json")
    except RuntimeError as exc:
        raise RuntimeError(f"cannot start next round: {exc}") from exc
    if str(state.get("status", "")) == "completed":
        print(
            json.dumps(
                {
                    "ok": False,
                    "run_id": args.run_id,
                    "reason": "run already completed",
                    "completion": state.get("completion"),
                },
                ensure_ascii=False,
            )
        )
        return

    generated = _run_json(["python", "-m", "app.cli.generate_round", "--run-id", args.run_id])
    round_no = int(generated["round_no"])
    draft = str(generated["draft"])

    validated = _run_json(
        [
            "python",
            "-m",
            "app.cli.validate_round",
            "--run-id",
            args.run_id,
            "--round-no",
            str(round_no),
            "--draft",
            draft,
            "--finalize",
        ]
    )

    print(
        json.dumps(
            {
                "ok": bool(validated.get("ok")),
                "run_id": args.run_id,
                "round_no": round_no,
                "draft": draft,
                "generation_package": generated.get("generation_package"),
                "final": validated.get("final"),
                "report": validated.get("report"),
                "completion": validated.get("completion"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
