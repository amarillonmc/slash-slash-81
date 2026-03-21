from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

INDEX_PATH = Path("boom-boom-81/kb/index/topics.jsonl")
CATEGORY_PATH_MAP: Dict[str, str] = {
    "roles": "kb/roles",
    "rulebooks": "kb/rulebooks",
    "records": "kb/records-completed",
}


@dataclass
class TopicEntry:
    title: str
    category: str
    path: str


def _extract_category(path: str) -> str:
    normalized = path.replace("\\", "/")
    for category, category_dir in CATEGORY_PATH_MAP.items():
        if category_dir in normalized:
            return category
    return "unknown"


def load_topics(index_path: Path = INDEX_PATH) -> List[TopicEntry]:
    if not index_path.exists():
        raise RuntimeError(f"topics index not found: {index_path}")

    topics: List[TopicEntry] = []
    with index_path.open("r", encoding="utf-8") as fp:
        for line in fp:
            raw = line.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            path = str(obj.get("path") or obj.get("file") or obj.get("file_path") or "")
            title = str(obj.get("title") or obj.get("topic") or "").strip()
            if not path or not title:
                continue
            topics.append(TopicEntry(title=title, category=_extract_category(path), path=path.replace("\\", "/")))
    return topics


def resolve_topics(titles: Iterable[str], category: str, topics: List[TopicEntry]) -> List[TopicEntry]:
    requested = {name.strip().lower() for name in titles if name.strip()}
    if not requested:
        return []

    selected = [item for item in topics if item.category == category and item.title.strip().lower() in requested]
    missing = requested - {item.title.strip().lower() for item in selected}
    if missing:
        raise RuntimeError(f"missing {category} entries in topics index: {sorted(missing)}")
    return sorted(selected, key=lambda x: x.title.lower())


def read_topic_markdown(path_in_repo: str) -> str:
    file_path = Path("boom-boom-81") / Path(path_in_repo)
    if not file_path.exists():
        raise RuntimeError(f"KB file not found: {file_path}")
    return file_path.read_text(encoding="utf-8")
