from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class ResolvedFile:
    category: str
    title: str
    source_path: str


@dataclass
class PromptBundle:
    director_system: str = "app/prompts/director_system.md"
    validator_system: str = "app/prompts/validator_system.md"
    qa_system: str = "app/prompts/qa_system.md"


@dataclass
class Manifest:
    run_id: str
    created_at: str
    rulebooks: List[str]
    rolesets: List[str]
    resolved_files: List[ResolvedFile]
    roles: List[str]
    prompt_bundle: PromptBundle = field(default_factory=PromptBundle)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["resolved_files"] = [asdict(item) for item in self.resolved_files]
        return data


@dataclass
class RoundHistoryItem:
    round_no: int
    draft_file: str
    final_file: str
    validation_file: str
    summary: str


@dataclass
class State:
    run_id: str
    current_round: int
    status: str
    alive_roles: List[str]
    eliminated_roles: List[str]
    round_history: List[RoundHistoryItem]
    public_summary: str
    private_notes: str
    updated_at: str
    completion: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["round_history"] = [asdict(item) if hasattr(item, "__dataclass_fields__") else item for item in self.round_history]
        return data


@dataclass
class ValidationReport:
    ok: bool
    errors: List[str]
    warnings: List[str]
    checks: Dict[str, bool]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
