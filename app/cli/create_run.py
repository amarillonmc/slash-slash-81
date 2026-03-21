from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from uuid import uuid4

from app.core.schemas import State, utc_now_iso
from app.core.state_store import ensure_run_layout, read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a new battle run with manifest/state.")
    parser.add_argument("--rulebooks", required=True, help="comma separated rulebook titles")
    parser.add_argument("--rolesets", required=True, help="comma separated roleset titles")
    parser.add_argument("--run-id", help="optional fixed run id")
    args = parser.parse_args()

    run_id = args.run_id or f"run-{utc_now_iso().replace(':', '').replace('-', '')}-{uuid4().hex[:6]}"
    run_dir = Path("runs") / run_id
    ensure_run_layout(run_dir)

    manifest_path = run_dir / "manifest.json"
    cmd = [
        "python",
        "-m",
        "app.cli.build_manifest",
        "--run-id",
        run_id,
        "--rulebooks",
        args.rulebooks,
        "--rolesets",
        args.rolesets,
        "--output",
        str(manifest_path),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "failed to build manifest")

    manifest = read_json(manifest_path)
    state = State(
        run_id=run_id,
        current_round=0,
        status="initialized",
        alive_roles=list(manifest.get("roles", [])),
        eliminated_roles=[],
        round_history=[],
        public_summary="Run created.",
        private_notes="",
        updated_at=utc_now_iso(),
        phase="opening",
        state_facts=["current_round=0", "phase=opening"],
        notable_events=["run_created"],
        unresolved_threads=["battle has not started"],
        uncertain_facts=[],
        extraction={"method": "initialization", "source": "create_run"},
        completion=None,
    )
    write_json(run_dir / "state.json", state.to_dict())

    print(
        json.dumps(
            {
                "ok": True,
                "run_id": run_id,
                "manifest": str(manifest_path),
                "state": str(run_dir / "state.json"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
