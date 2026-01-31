"""Tests for the decision engine."""

import pytest

from src.review.state import ReviewFinding, Severity, Category
from src.review.nodes.decision_engine import decision_engine, get_decision_summary


class TestDecisionEngine:
    """Tests for the decision engine logic."""

    @pytest.mark.asyncio
    async def test_pass_with_no_findings(self):
        state = {
            "findings": [],
            "pr_metadata": None,
        }
        result = await decision_engine(state)
        assert result["decision"] == "PASS"
        assert result["confidence_score"] >= 0.7

    @pytest.mark.asyncio
    async def test_fail_with_blocking_issue(self):
        state = {
            "findings": [
                ReviewFinding(
                    severity=Severity.BLOCKING,
                    category=Category.CORRECTNESS,
                    title="Null pointer",
                    description="Missing null check",
                    confidence=0.9,
                )
            ],
            "pr_metadata": None,
        }
        result = await decision_engine(state)
        assert result["decision"] == "FAIL"

    @pytest.mark.asyncio
    async def test_pass_with_only_suggestions(self):
        state = {
            "findings": [
                ReviewFinding(
                    severity=Severity.SUGGESTION,
                    category=Category.ENGINEERING_QUALITY,
                    title="Consider adding type hints",
                    description="Type hints improve readability",
                    confidence=0.8,
                ),
                ReviewFinding(
                    severity=Severity.NON_BLOCKING,
                    category=Category.PRODUCTION_READINESS,
                    title="Missing logging",
                    description="Add logging for debugging",
                    confidence=0.7,
                ),
            ],
            "pr_metadata": None,
        }
        result = await decision_engine(state)
        assert result["decision"] == "PASS"

    @pytest.mark.asyncio
    async def test_fail_with_mixed_findings(self):
        state = {
            "findings": [
                ReviewFinding(
                    severity=Severity.SUGGESTION,
                    category=Category.ENGINEERING_QUALITY,
                    title="Minor improvement",
                    description="Nice to have",
                    confidence=0.6,
                ),
                ReviewFinding(
                    severity=Severity.BLOCKING,
                    category=Category.SECURITY,
                    title="Hardcoded secret",
                    description="API key in source code",
                    confidence=0.95,
                ),
            ],
            "pr_metadata": None,
        }
        result = await decision_engine(state)
        assert result["decision"] == "FAIL"


class TestGetDecisionSummary:
    """Tests for decision summary generation."""

    def test_summary_format(self):
        state = {
            "decision": "FAIL",
            "confidence_score": 0.85,
            "findings": [
                ReviewFinding(
                    severity=Severity.BLOCKING,
                    category=Category.CORRECTNESS,
                    title="Bug",
                    description="A bug",
                    confidence=0.9,
                ),
                ReviewFinding(
                    severity=Severity.NON_BLOCKING,
                    category=Category.ENGINEERING_QUALITY,
                    title="Improvement",
                    description="An improvement",
                    confidence=0.8,
                ),
            ],
        }
        summary = get_decision_summary(state)
        assert "FAIL" in summary
        assert "85%" in summary
        assert "Blocking issues: 1" in summary
