from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def ensure_run_layout(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "rounds").mkdir(exist_ok=True)
    (run_dir / "qa").mkdir(exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2, sort_keys=False)
        fp.write("\n")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"file not found: {path}")
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)
