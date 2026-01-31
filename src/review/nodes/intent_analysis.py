"""Intent analysis node - understands what the PR is trying to accomplish."""

from __future__ import annotations

import json
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.review.state import ReviewState


SYSTEM_PROMPT = """You are a senior software engineer analyzing a Pull Request to understand its intent.

Your task is to:
1. Summarize what this PR is trying to accomplish in 2-3 sentences
2. Identify the main areas of change (new features, bug fixes, refactoring, etc.)
3. Assess the risk level (low, medium, high) based on the scope of changes

Output your analysis as JSON with this structure:
{
    "summary": "Brief description of what this PR does",
    "change_type": "feature|bugfix|refactor|docs|test|chore",
    "risk_level": "low|medium|high",
    "areas_affected": ["list", "of", "affected", "areas"],
    "key_concerns": ["list of things to watch out for during review"]
}

Be concise and focus on the most important information."""


async def intent_analysis(state: ReviewState, llm: ChatOpenAI) -> Dict:
    """Analyze the PR to understand its intent.

    Args:
        state: Current review state.
        llm: The LLM to use for analysis.

    Returns:
        Updated state with intent summary.
    """
    pr_info = state["pr_metadata"]

    user_message = f"""# Pull Request: {pr_info.title}

## Description
{pr_info.description or "No description provided."}

## Files Changed ({len(pr_info.files_changed)} files, +{pr_info.additions}/-{pr_info.deletions})
{chr(10).join(f"- {f}" for f in pr_info.files_changed[:20])}
{"... and more files" if len(pr_info.files_changed) > 20 else ""}

## Diff
```diff
{state["pr_diff"][:8000]}
```
{"... (diff truncated)" if len(state["pr_diff"]) > 8000 else ""}
"""

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    # Parse the JSON response
    try:
        content = response.content
        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        analysis = json.loads(content.strip())
        summary = f"""**Intent**: {analysis.get('summary', 'Unable to determine')}

**Change Type**: {analysis.get('change_type', 'unknown')}
**Risk Level**: {analysis.get('risk_level', 'unknown')}
**Areas Affected**: {', '.join(analysis.get('areas_affected', []))}

**Key Concerns**:
{chr(10).join(f"- {c}" for c in analysis.get('key_concerns', []))}"""
    except (json.JSONDecodeError, KeyError):
        summary = f"Intent analysis: {response.content[:500]}"

    return {
        "intent_summary": summary,
        "current_stage": "intent_analysis",
    }
