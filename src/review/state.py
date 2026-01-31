"""State definitions for the review pipeline."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Optional, Tuple, TypedDict

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Issue severity levels."""

    BLOCKING = "BLOCKING"
    NON_BLOCKING = "NON_BLOCKING"
    SUGGESTION = "SUGGESTION"


class Category(str, Enum):
    """Issue categories."""

    CORRECTNESS = "correctness"
    ENGINEERING_QUALITY = "engineering_quality"
    PRODUCTION_READINESS = "production_readiness"
    SECURITY = "security"


class ReviewFinding(BaseModel):
    """A single finding from the review process."""

    severity: Severity = Field(description="The severity level of the issue")
    category: Category = Field(description="The category of the issue")
    title: str = Field(description="Short title describing the issue")
    description: str = Field(description="Detailed description of the issue")
    file_path: Optional[str] = Field(default=None, description="File where the issue was found")
    line_start: Optional[int] = Field(default=None, description="Starting line number")
    line_end: Optional[int] = Field(default=None, description="Ending line number")
    code_snippet: Optional[str] = Field(default=None, description="Relevant code snippet")
    suggested_fix: Optional[str] = Field(default=None, description="Suggested fix for the issue")
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence score for this finding"
    )


class PRInfo(BaseModel):
    """Information about the pull request being reviewed."""

    number: int
    title: str
    description: Optional[str]
    author: str
    base_branch: str
    head_branch: str
    files_changed: List[str]
    additions: int
    deletions: int
    url: str


def merge_findings(
    existing: List[ReviewFinding], new: List[ReviewFinding]
) -> List[ReviewFinding]:
    """Merge two lists of findings, avoiding duplicates."""
    # Simple merge - in production you might dedupe by content
    return existing + new


class ReviewState(TypedDict):
    """State passed through the review pipeline."""

    # Input data
    pr_diff: str
    pr_metadata: PRInfo
    languages: List[str]

    # Pipeline outputs (accumulated)
    intent_summary: str
    findings: Annotated[List[ReviewFinding], merge_findings]

    # Final outputs
    decision: str  # "PASS", "FAIL", or "ERROR"
    confidence_score: float
    markdown_report: str
    docx_report_path: Optional[str]

    # Workflow tracking
    current_stage: str
    error_message: Optional[str]
