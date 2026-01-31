from __future__ import annotations

import json
from typing import Dict, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.review.state import ReviewState, ReviewFinding, Severity, Category
from src.review.prompts import get_combined_criteria


SYSTEM_PROMPT = """You are a senior engineer reviewing code for production readiness.

Focus on:
- Hardcoded secrets or API keys
- Missing logging
- Missing error handling
- Security vulnerabilities (SQL injection, XSS)
- Missing timeouts on external calls
- Configuration not externalized

Respond in JSON:
{
    "findings": [
        {
            "severity": "BLOCKING|NON_BLOCKING|SUGGESTION",
            "title": "Brief title",
            "description": "Detailed explanation",
            "file_path": "path/to/file.py",
            "line_start": 42,
            "line_end": 45,
            "code_snippet": "problematic code",
            "suggested_fix": "how to fix it",
            "confidence": 0.9
        }
    ]
}

Severity guide:
- BLOCKING: Security issues, hardcoded secrets, missing critical error handling
- NON_BLOCKING: Missing logging, missing timeouts
- SUGGESTION: Nice to have improvements
"""


async def production_readiness_review(state: ReviewState, llm: ChatOpenAI) -> Dict:
    diff = state["pr_diff"]
    languages = state.get("languages", [])
    criteria = get_combined_criteria(languages)

    user_message = f"""
Review this code diff for production readiness:

{criteria}

---

Diff:
{diff[:12000]}
"""

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    findings = _parse_findings(response.content, Category.PRODUCTION_READINESS)

    return {
        "findings": findings,
        "current_stage": "production_readiness_review",
    }


def _parse_findings(content: str, category: Category) -> List[ReviewFinding]:
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        data = json.loads(content.strip())
        findings = []

        for item in data.get("findings", []):
            severity_str = item.get("severity", "NON_BLOCKING").upper()
            severity = Severity(severity_str) if severity_str in ["BLOCKING", "NON_BLOCKING", "SUGGESTION"] else Severity.NON_BLOCKING

            findings.append(ReviewFinding(
                severity=severity,
                category=category,
                title=item.get("title", "Unknown Issue"),
                description=item.get("description", ""),
                file_path=item.get("file_path"),
                line_start=item.get("line_start"),
                line_end=item.get("line_end"),
                code_snippet=item.get("code_snippet"),
                suggested_fix=item.get("suggested_fix"),
                confidence=item.get("confidence", 0.8),
            ))

        return findings
    except (json.JSONDecodeError, KeyError, TypeError):
        return []
