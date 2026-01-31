"""Production readiness review node - checks for operational concerns."""

from __future__ import annotations

import json
from typing import Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.review.prompts import get_combined_criteria
from src.review.state import Category, ReviewFinding, ReviewState, Severity


SYSTEM_PROMPT = """You are a senior SRE/DevOps engineer reviewing code for production readiness.

Your task is to identify issues that could cause problems when this code runs in production.

Look for:
1. Hardcoded secrets, API keys, or credentials
2. Missing logging for important operations
3. Missing timeout configuration on HTTP/database calls
4. Environment variables not used for configuration
5. Missing health checks or observability hooks
6. Not handling transient failures (missing retries)
7. Security issues (SQL injection, XSS, SSRF potential)
8. Missing rate limiting on public endpoints

{language_criteria}

For each issue found, output JSON in this format:
{{
    "findings": [
        {{
            "severity": "BLOCKING|NON_BLOCKING|SUGGESTION",
            "title": "Short title",
            "description": "Detailed explanation of the issue",
            "file_path": "path/to/file.py",
            "line_start": 42,
            "line_end": 45,
            "code_snippet": "the problematic code",
            "suggested_fix": "how to fix it",
            "confidence": 0.9
        }}
    ]
}}

Guidelines:
- BLOCKING: Security issues, hardcoded secrets, or issues that will cause outages
- NON_BLOCKING: Missing logging, timeouts, or observability
- SUGGESTION: Nice-to-have operational improvements
- Be VERY strict about hardcoded secrets - this is always BLOCKING

If no issues are found, return: {{"findings": []}}"""


async def production_readiness_review(state: ReviewState, llm: ChatOpenAI) -> Dict:
    """Review the PR for production readiness.

    Args:
        state: Current review state.
        llm: The LLM to use for analysis.

    Returns:
        Updated state with production readiness findings.
    """
    language_criteria = get_combined_criteria(state["languages"])

    system_prompt = SYSTEM_PROMPT.format(language_criteria=language_criteria)

    user_message = f"""# Code Review: Production Readiness Analysis

## PR Context
{state["intent_summary"]}

## Languages
{', '.join(state["languages"]) or "General"}

## Diff to Review
```diff
{state["pr_diff"][:12000]}
```
{"... (diff truncated)" if len(state["pr_diff"]) > 12000 else ""}

Identify any production readiness issues in this diff."""

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ])

    findings = _parse_findings(response.content, Category.PRODUCTION_READINESS)

    return {
        "findings": findings,
        "current_stage": "production_readiness_review",
    }


def _parse_findings(content: str, category: Category) -> List[ReviewFinding]:
    """Parse LLM response into ReviewFinding objects."""
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        data = json.loads(content.strip())
        findings = []

        for item in data.get("findings", []):
            severity_str = item.get("severity", "SUGGESTION").upper()
            try:
                severity = Severity(severity_str)
            except ValueError:
                severity = Severity.SUGGESTION

            findings.append(
                ReviewFinding(
                    severity=severity,
                    category=category,
                    title=item.get("title", "Untitled issue"),
                    description=item.get("description", "No description"),
                    file_path=item.get("file_path"),
                    line_start=item.get("line_start"),
                    line_end=item.get("line_end"),
                    code_snippet=item.get("code_snippet"),
                    suggested_fix=item.get("suggested_fix"),
                    confidence=item.get("confidence", 0.8),
                )
            )

        return findings

    except (json.JSONDecodeError, KeyError, TypeError):
        return []
