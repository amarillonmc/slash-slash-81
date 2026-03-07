from __future__ import annotations

from typing import Dict, List

from app.core.schemas import ValidationReport


def validate_round_text(round_text: str, alive_roles: List[str], expected_round: int) -> ValidationReport:
    errors: List[str] = []
    warnings: List[str] = []

    checks: Dict[str, bool] = {
        "non_empty": bool(round_text.strip()),
        "has_round_header": f"Round {expected_round}" in round_text,
        "mentions_alive_role": any(role in round_text for role in alive_roles),
    }

    if not checks["non_empty"]:
        errors.append("round text is empty")
    if not checks["has_round_header"]:
        errors.append(f"round text must include header 'Round {expected_round}'")
    if alive_roles and not checks["mentions_alive_role"]:
        warnings.append("round text does not explicitly mention any alive role")

    return ValidationReport(ok=len(errors) == 0, errors=errors, warnings=warnings, checks=checks)
