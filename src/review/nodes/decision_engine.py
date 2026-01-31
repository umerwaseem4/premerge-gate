"""Decision engine node."""

from __future__ import annotations

from typing import Dict

from src.review.state import ReviewState, Severity


async def decision_engine(state: ReviewState) -> Dict:
    findings = state.get("findings", [])

    blocking_count = sum(1 for f in findings if f.severity == Severity.BLOCKING)
    non_blocking_count = sum(1 for f in findings if f.severity == Severity.NON_BLOCKING)
    suggestion_count = sum(1 for f in findings if f.severity == Severity.SUGGESTION)

    if blocking_count > 0:
        decision = "FAIL"
    else:
        decision = "PASS"

    if findings:
        avg_confidence = sum(f.confidence for f in findings) / len(findings)
    else:
        avg_confidence = 1.0

    return {
        "decision": decision,
        "confidence_score": avg_confidence,
        "current_stage": "decision_engine",
    }


def get_decision_summary(state: ReviewState) -> str:
    findings = state.get("findings", [])
    decision = state.get("decision", "UNKNOWN")

    blocking = sum(1 for f in findings if f.severity == Severity.BLOCKING)
    non_blocking = sum(1 for f in findings if f.severity == Severity.NON_BLOCKING)
    suggestions = sum(1 for f in findings if f.severity == Severity.SUGGESTION)

    return f"""
Decision: {decision}
Blocking Issues: {blocking}
Non-Blocking Issues: {non_blocking}
Suggestions: {suggestions}
Total Findings: {len(findings)}
""".strip()
