from __future__ import annotations

import re
from typing import Any, Dict, List

COMPLETION_KEYWORDS = [
    "乱斗结束",
    "剧终",
    "胜负已定",
    "任务完成",
    "故事到此结束",
    "最终回",
    "the end",
]




def _focus_narrative(text: str) -> str:
    marker = "## Round Narrative"
    if marker not in text:
        return text
    part = text.split(marker, 1)[1]
    if "##" in part:
        part = part.split("##", 1)[0]
    return part

def _keyword_signals(text: str) -> List[str]:
    lower = text.lower()
    found: List[str] = []
    for keyword in COMPLETION_KEYWORDS:
        if keyword.lower() in lower:
            found.append(keyword)
    return found


def _extract_winner_like_entities(text: str, roles: List[str]) -> List[str]:
    winners: List[str] = []
    lowered = text.lower()
    for role in roles:
        if not role:
            continue
        role_l = role.lower()
        patterns = [
            rf"{re.escape(role_l)}.*(获胜|胜利|surviv|赢家|winner)",
            rf"(获胜|胜利|surviv|赢家|winner).+{re.escape(role_l)}",
        ]
        if any(re.search(pattern, lowered) for pattern in patterns):
            winners.append(role)
    return sorted(set(winners))


def assess_completion(
    round_text: str,
    previous_finals: List[str],
    rulebook_titles: List[str],
    roles: List[str],
    state_status: str,
) -> Dict[str, Any]:
    focused_text = _focus_narrative(round_text)
    signals = _keyword_signals(focused_text)
    winners = _extract_winner_like_entities(focused_text, roles)

    prior_tail = "\n".join(previous_finals[-2:]).lower()
    repeated_end_signal = any(keyword.lower() in prior_tail for keyword in COMPLETION_KEYWORDS) and bool(signals)

    rule_context_present = bool(rulebook_titles)
    lower_text = focused_text.lower()
    terminal_phrase = any(token in lower_text for token in ["剧终", "乱斗结束", "故事到此结束", "the end"])
    strong_signal = bool(signals) and (bool(winners) or repeated_end_signal or terminal_phrase)

    is_complete = state_status != "completed" and strong_signal and rule_context_present

    reason = "no completion signal"
    if is_complete:
        reason = "completion signals detected in round text with winner/end-state evidence"
    elif signals and not rule_context_present:
        reason = "completion-like text found but no rulebook context loaded"
    elif signals:
        reason = "completion-like text found but confidence is low"

    summary = "对局进行中。"
    if is_complete:
        winner_text = "、".join(winners) if winners else "未明确单一赢家"
        summary = f"演绎已完成：{reason}；结果：{winner_text}。"

    return {
        "is_complete": is_complete,
        "reason": reason,
        "signals": signals,
        "winner_like_entities": winners,
        "summary": summary,
    }
