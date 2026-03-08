from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from app.core.kb_index import load_topics, resolve_topics
from app.core.schemas import Manifest, ResolvedFile, utc_now_iso


def parse_csv(value: str) -> List[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build run manifest from topic index.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--rulebooks", required=True, help="comma separated rulebook titles")
    parser.add_argument("--rolesets", required=True, help="comma separated roleset titles")
    parser.add_argument("--output", required=True, help="manifest output path")
    args = parser.parse_args()

    topics = load_topics()
    rulebooks = parse_csv(args.rulebooks)
    rolesets = parse_csv(args.rolesets)

    resolved_rulebooks = resolve_topics(rulebooks, "rulebooks", topics)
    resolved_rolesets = resolve_topics(rolesets, "roles", topics)

    resolved_files = [
        ResolvedFile(category=item.category, title=item.title, source_path=item.path)
        for item in [*resolved_rulebooks, *resolved_rolesets]
    ]

    manifest = Manifest(
        run_id=args.run_id,
        created_at=utc_now_iso(),
        rulebooks=rulebooks,
        rolesets=rolesets,
        resolved_files=resolved_files,
        roles=[item.title for item in resolved_rolesets],
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as fp:
        json.dump(manifest.to_dict(), fp, ensure_ascii=False, indent=2)
        fp.write("\n")

    print(json.dumps({"ok": True, "manifest": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
