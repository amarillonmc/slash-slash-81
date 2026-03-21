from __future__ import annotations

import re
from typing import Any, Dict, List

from app.core.completion import assess_completion

STATE_EVENT_KEYWORDS = ["淘汰", "出局", "死亡", "阵亡", "获胜", "胜利", "联盟", "背叛", "暴露", "线索", "任务"]
PHASE_KEYWORDS = [("opening", ["开场", "第 1 回合", "第1回合"]), ("midgame", ["僵持", "推进", "升级"]), ("endgame", ["最终回", "终局", "剧终", "乱斗结束"])]


def _bullet_lines(text: str) -> List[str]:
    lines: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("-", "*")):
            lines.append(line.lstrip("-* "))
    return lines


def _detect_eliminations(text: str, roles: List[str]) -> Dict[str, List[str]]:
    alive: List[str] = []
    eliminated: List[str] = []
    uncertain: List[str] = []
    lower = text.lower()
    for role in roles:
        if not role:
            continue
        role_lower = role.lower()
        if role_lower not in lower:
            continue
        eliminated_pattern = rf"{re.escape(role)}[^。！？\n]{{0,24}}(淘汰|出局|死亡|阵亡)"
        alive_pattern = rf"{re.escape(role)}[^。！？\n]{{0,24}}(存活|仍在场|继续行动|幸存)"
        if re.search(eliminated_pattern, text):
            eliminated.append(role)
        elif re.search(alive_pattern, text):
            alive.append(role)
        else:
            uncertain.append(role)
    return {"alive": sorted(set(alive)), "eliminated": sorted(set(eliminated)), "uncertain": sorted(set(uncertain))}


def _choose_phase(round_text: str, round_no: int, completion_report: Dict[str, Any]) -> str:
    lower = round_text.lower()
    if completion_report.get("is_complete"):
        return "completed"
    for phase, keywords in PHASE_KEYWORDS:
        if any(keyword.lower() in lower for keyword in keywords):
            return phase
    if round_no <= 1:
        return "opening"
    if round_no >= 3:
        return "endgame"
    return "midgame"


def extract_state_update(
    round_text: str,
    round_no: int,
    manifest: Dict[str, Any],
    previous_state: Dict[str, Any],
    previous_final: str = "",
) -> Dict[str, Any]:
    roles = list(manifest.get("roles", []))
    completion_report = assess_completion(
        round_text=round_text,
        previous_finals=[previous_final] if previous_final else [],
        rulebook_titles=list(manifest.get("rulebooks", [])),
        roles=roles,
        state_status=str(previous_state.get("status", "initialized")),
    )

    detected = _detect_eliminations(round_text, roles)
    prior_alive = list(previous_state.get("alive_roles", []))
    prior_eliminated = list(previous_state.get("eliminated_roles", []))

    eliminated_roles = sorted(set(prior_eliminated + detected["eliminated"]))
    alive_candidates = detected["alive"] or [role for role in prior_alive if role not in eliminated_roles]
    alive_roles = sorted([role for role in alive_candidates if role not in eliminated_roles])

    event_lines = [line for line in _bullet_lines(round_text) if any(keyword in line for keyword in STATE_EVENT_KEYWORDS)]
    notable_events = event_lines[:6]
    if not notable_events:
        narrative_lines = [line.strip() for line in round_text.splitlines() if line.strip() and not line.startswith("#")]
        notable_events = narrative_lines[:3]

    summary_parts = [f"第 {round_no} 回合已落盘。"]
    if notable_events:
        summary_parts.append("关键进展：" + "；".join(notable_events[:2]))
    if eliminated_roles:
        summary_parts.append("已淘汰：" + "、".join(eliminated_roles))
    public_summary = " ".join(summary_parts)

    unresolved_threads = []
    if detected["uncertain"]:
        unresolved_threads.append("以下角色状态尚不明确：" + "、".join(detected["uncertain"][:4]))
    if not completion_report.get("is_complete"):
        unresolved_threads.append("胜负与终局条件尚未完全确认")

    phase = _choose_phase(round_text, round_no, completion_report)
    state_facts = [f"current_round={round_no}", f"phase={phase}"]
    state_facts.extend([f"eliminated:{role}" for role in eliminated_roles])
    state_facts.extend([f"alive:{role}" for role in alive_roles])

    private_notes = str(previous_state.get("private_notes", "")).strip()
    if completion_report.get("signals"):
        signal_note = "completion_signals=" + ",".join(completion_report["signals"])
        private_notes = f"{private_notes}\n{signal_note}".strip()

    extraction = {
        "method": "heuristic_text_extraction",
        "round_no": round_no,
        "completion_inputs": {
            "rulebooks": list(manifest.get("rulebooks", [])),
            "roles": roles,
            "previous_final_present": bool(previous_final),
        },
        "detected_alive": alive_roles,
        "detected_eliminated": eliminated_roles,
        "uncertain_roles": detected["uncertain"],
        "events": notable_events,
    }

    return {
        "current_round": round_no,
        "status": "completed" if completion_report.get("is_complete") else "in_progress",
        "phase": phase,
        "public_summary": public_summary,
        "private_notes": private_notes,
        "alive_roles": alive_roles,
        "eliminated_roles": eliminated_roles,
        "state_facts": state_facts,
        "notable_events": notable_events,
        "unresolved_threads": unresolved_threads,
        "uncertain_facts": [f"role_status_uncertain:{role}" for role in detected["uncertain"]],
        "extraction": extraction,
        "completion": completion_report,
    }
