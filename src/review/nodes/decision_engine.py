"""Decision engine node - determines PASS or FAIL based on findings."""

from __future__ import annotations

from typing import Dict, List

from src.review.state import ReviewFinding, ReviewState, Severity


async def decision_engine(state: ReviewState) -> Dict:
    """Make a final decision based on all review findings.

    The decision logic is deterministic:
    - If ANY finding has severity=BLOCKING, the review FAILS
    - Otherwise, the review PASSES

    Args:
        state: Current review state with accumulated findings.

    Returns:
        Updated state with decision and confidence score.
    """
    findings = state.get("findings", [])

    # Count findings by severity
    blocking_count = sum(1 for f in findings if f.severity == Severity.BLOCKING)
    non_blocking_count = sum(1 for f in findings if f.severity == Severity.NON_BLOCKING)
    suggestion_count = sum(1 for f in findings if f.severity == Severity.SUGGESTION)

    # Make decision
    if blocking_count > 0:
        decision = "FAIL"
    else:
        decision = "PASS"

    # Calculate confidence score based on finding confidence values
    if findings:
        avg_confidence = sum(f.confidence for f in findings) / len(findings)
    else:
        avg_confidence = 0.9  # High confidence if no issues found

    # Adjust base confidence
    if decision == "FAIL":
        # Higher confidence when we found blocking issues
        confidence_score = min(0.95, avg_confidence + 0.1)
    else:
        # Slightly lower confidence for PASS (we might have missed something)
        confidence_score = max(0.7, avg_confidence - 0.1)

    return {
        "decision": decision,
        "confidence_score": round(confidence_score, 2),
        "current_stage": "decision_engine",
    }


def get_decision_summary(state: ReviewState) -> str:
    """Generate a summary of the decision for logging.

    Args:
        state: The review state with decision.

    Returns:
        Human-readable decision summary.
    """
    findings = state.get("findings", [])
    decision = state.get("decision", "UNKNOWN")

    blocking = [f for f in findings if f.severity == Severity.BLOCKING]
    non_blocking = [f for f in findings if f.severity == Severity.NON_BLOCKING]
    suggestions = [f for f in findings if f.severity == Severity.SUGGESTION]

    lines = [
        f"Decision: {decision}",
        f"Confidence: {state.get('confidence_score', 0):.0%}",
        f"Blocking issues: {len(blocking)}",
        f"Non-blocking issues: {len(non_blocking)}",
        f"Suggestions: {len(suggestions)}",
    ]

    return "\n".join(lines)
