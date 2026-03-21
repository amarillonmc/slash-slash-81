from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.core.schemas import ValidationReport

PLACEHOLDER_PATTERNS = [
    r"TODO",
    r"TBD",
    r"<[^>]+>",
    r"OpenCode should rewrite",
    r"请在此补充",
    r"待补充",
    r"lorem ipsum",
]


def _check(name: str, ok: bool, details: str, severity: str = "error") -> Dict[str, Any]:
    return {"ok": ok, "details": details, "severity": severity}


def _extract_previous_facts(previous_final: str, alive_roles: List[str], eliminated_roles: List[str]) -> List[str]:
    facts: List[str] = []
    haystack = previous_final.lower()
    for role in alive_roles:
        if role and role.lower() in haystack:
            facts.append(f"previous round referenced alive role {role}")
    for role in eliminated_roles:
        if role and role.lower() in haystack:
            facts.append(f"previous round referenced eliminated role {role}")
    return facts


def validate_round_text(
    round_text: str,
    alive_roles: List[str],
    expected_round: int,
    previous_final: str = "",
    eliminated_roles: Optional[List[str]] = None,
    sources_considered: Optional[List[str]] = None,
) -> ValidationReport:
    eliminated = eliminated_roles or []
    sources = sources_considered or []
    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, Dict[str, Any]] = {}

    stripped = round_text.strip()
    checks["structure.non_empty"] = _check("structure.non_empty", bool(stripped), "round text must not be empty")
    checks["structure.round_header"] = _check(
        "structure.round_header",
        f"# Round {expected_round}" in round_text or f"Round {expected_round}" in round_text,
        f"round text must include header for Round {expected_round}",
    )
    narrative_lines = [line.strip() for line in round_text.splitlines() if line.strip() and not line.strip().startswith("#")]
    checks["narrative.min_length"] = _check(
        "narrative.min_length",
        len(narrative_lines) >= 6 and len(stripped) >= 180,
        "round narrative is too short for MVP-2 quality",
        severity="warning",
    )

    mentioned_alive = [role for role in alive_roles if role and role in round_text]
    checks["roles.key_roles_mentioned"] = _check(
        "roles.key_roles_mentioned",
        bool(mentioned_alive) if alive_roles else True,
        "round text should mention at least one alive role",
        severity="warning",
    )

    acted_eliminated = []
    for role in eliminated:
        if role and role in round_text and re.search(rf"{re.escape(role)}.*(行动|出手|反击|发言|存活)", round_text):
            acted_eliminated.append(role)
    checks["roles.eliminated_not_active"] = _check(
        "roles.eliminated_not_active",
        not acted_eliminated,
        "eliminated roles should not be described as normal active actors",
    )

    placeholder_hits = [pattern for pattern in PLACEHOLDER_PATTERNS if re.search(pattern, round_text, flags=re.IGNORECASE)]
    checks["narrative.no_placeholders"] = _check(
        "narrative.no_placeholders",
        not placeholder_hits,
        "round text still contains placeholders or prompt leakage",
    )

    prior_round_ref = previous_final and ("上一回合" in round_text or "延续" in round_text or "此前" in round_text)
    continuity_ok = True
    continuity_details = "no previous final available"
    if previous_final:
        previous_facts = _extract_previous_facts(previous_final, alive_roles, eliminated)
        continuity_ok = prior_round_ref or bool(previous_facts)
        continuity_details = "round should acknowledge previous state or known participants"
    checks["continuity.references_previous_state"] = _check(
        "continuity.references_previous_state",
        continuity_ok,
        continuity_details,
        severity="warning",
    )

    impossible_ref = re.findall(r"第\s*([0-9]+)\s*回合", round_text)
    impossible_numbers = [ref for ref in impossible_ref if int(ref) > expected_round]
    checks["continuity.no_future_reference"] = _check(
        "continuity.no_future_reference",
        not impossible_numbers,
        "round text references future rounds that do not exist yet",
    )

    required_categories = {"rulebooks", "roles"}
    present_categories = {source.split(":", 1)[0] for source in sources if ":" in source}
    checks["references.required_sources_loaded"] = _check(
        "references.required_sources_loaded",
        required_categories.issubset(present_categories),
        "validation should report rulebooks and roles sources",
        severity="warning",
    )

    for name, info in checks.items():
        if info["ok"]:
            continue
        if info["severity"] == "error":
            errors.append(f"{name}: {info['details']}")
        else:
            warnings.append(f"{name}: {info['details']}")

    summary = (
        f"Validation {'passed' if not errors else 'failed'} with "
        f"{len(errors)} error(s), {len(warnings)} warning(s), and {len(sources)} source(s) considered."
    )
    return ValidationReport(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        checks=checks,
        sources_considered=sources,
        summary=summary,
    )
