"""Bug and logic review node - checks for correctness issues."""

from __future__ import annotations

import json
from typing import Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.review.prompts import get_combined_criteria
from src.review.state import Category, ReviewFinding, ReviewState, Severity


SYSTEM_PROMPT = """You are a senior software engineer performing a code review focused on correctness and logic errors.

Your task is to identify bugs, logic errors, and correctness issues in the code diff provided.

Look for:
1. Null/undefined reference errors
2. Off-by-one errors
3. Incorrect conditional logic
4. Edge cases not handled (empty arrays, zero values, negative numbers)
5. Type mismatches or incorrect assumptions
6. Race conditions or concurrency issues
7. Incorrect error handling

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
- Use BLOCKING for issues that will definitely cause bugs in production
- Use NON_BLOCKING for potential issues that should be addressed
- Use SUGGESTION for style improvements or minor concerns
- Set confidence based on how certain you are (0.5-1.0)
- Say "UNCERTAIN" in the description if you need more context
- Do NOT flag issues that don't exist in the diff
- Be specific about file paths and line numbers when possible

If no issues are found, return: {{"findings": []}}"""


async def bug_logic_review(state: ReviewState, llm: ChatOpenAI) -> Dict:
    """Review the PR for bugs and logic errors.

    Args:
        state: Current review state.
        llm: The LLM to use for analysis.

    Returns:
        Updated state with bug/logic findings.
    """
    language_criteria = get_combined_criteria(state["languages"])

    system_prompt = SYSTEM_PROMPT.format(language_criteria=language_criteria)

    user_message = f"""# Code Review: Bug and Logic Analysis

## PR Context
{state["intent_summary"]}

## Languages
{', '.join(state["languages"]) or "General"}

## Diff to Review
```diff
{state["pr_diff"][:12000]}
```
{"... (diff truncated)" if len(state["pr_diff"]) > 12000 else ""}

Identify any bugs, logic errors, or correctness issues in this diff."""

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ])

    findings = _parse_findings(response.content, Category.CORRECTNESS)

    return {
        "findings": findings,
        "current_stage": "bug_logic_review",
    }


def _parse_findings(content: str, category: Category) -> List[ReviewFinding]:
    """Parse LLM response into ReviewFinding objects.

    Args:
        content: The LLM response content.
        category: The category to assign to findings.

    Returns:
        List of ReviewFinding objects.
    """
    try:
        # Handle markdown code blocks
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
        # If parsing fails, return empty list
        return []
