"""Engineering quality review node - checks for best practices."""

from __future__ import annotations

import json
from typing import Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.review.prompts import get_combined_criteria
from src.review.state import Category, ReviewFinding, ReviewState, Severity


SYSTEM_PROMPT = """You are a senior software engineer reviewing code for engineering quality and best practices.

Your task is to identify engineering quality issues that could cause problems at scale or during maintenance.

Look for:
1. Missing pagination on list/query operations
2. N+1 query patterns (database queries in loops)
3. Missing input validation
4. Improper error handling (catching generic exceptions, swallowing errors)
5. Performance anti-patterns (unbounded loops, excessive allocations)
6. Missing type safety / type hints
7. Code duplication that should be abstracted
8. Async/await issues (blocking calls in async context)

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
- BLOCKING: Issues that will cause production outages or data loss at scale
- NON_BLOCKING: Best practice violations that should be fixed
- SUGGESTION: Improvements that would be nice to have
- Be specific about WHY something is a problem
- Provide actionable fixes

If no issues are found, return: {{"findings": []}}"""


async def engineering_quality_review(state: ReviewState, llm: ChatOpenAI) -> Dict:
    """Review the PR for engineering quality issues.

    Args:
        state: Current review state.
        llm: The LLM to use for analysis.

    Returns:
        Updated state with engineering quality findings.
    """
    language_criteria = get_combined_criteria(state["languages"])

    system_prompt = SYSTEM_PROMPT.format(language_criteria=language_criteria)

    user_message = f"""# Code Review: Engineering Quality Analysis

## PR Context
{state["intent_summary"]}

## Languages
{', '.join(state["languages"]) or "General"}

## Diff to Review
```diff
{state["pr_diff"][:12000]}
```
{"... (diff truncated)" if len(state["pr_diff"]) > 12000 else ""}

Identify any engineering quality issues in this diff."""

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ])

    findings = _parse_findings(response.content, Category.ENGINEERING_QUALITY)

    return {
        "findings": findings,
        "current_stage": "engineering_quality_review",
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
