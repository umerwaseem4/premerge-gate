"""Intent analysis node."""

from __future__ import annotations

import json
from typing import Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.review.state import ReviewState


SYSTEM_PROMPT = """You are a senior code reviewer analyzing a Pull Request.
Your task is to understand the intent and scope of the changes.

Respond in JSON format:
{
    "summary": "Brief description of what this PR does",
    "change_type": "feature|bugfix|refactor|docs|test|chore",
    "risk_level": "low|medium|high|critical",
    "areas_affected": ["list", "of", "areas"],
    "key_concerns": ["list", "of", "potential", "concerns"]
}
"""


async def intent_analysis(state: ReviewState, llm: ChatOpenAI) -> Dict:
    pr_info = state["pr_metadata"]
    diff = state["pr_diff"]
    languages = state.get("languages", [])

    user_message = f"""
PR Title: {pr_info.title}
PR Description: {pr_info.description or "No description"}
Author: {pr_info.author}
Target: {pr_info.base_branch} <- {pr_info.head_branch}
Languages: {', '.join(languages) if languages else 'Unknown'}
Files Changed: {len(pr_info.files_changed)}
Changes: +{pr_info.additions} / -{pr_info.deletions}

Diff:
{diff[:8000]}
"""

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    try:
        content = response.content
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
