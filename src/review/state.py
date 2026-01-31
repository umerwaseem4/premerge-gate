from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Optional, TypedDict

from pydantic import BaseModel, Field


class Severity(str, Enum):
    BLOCKING = "BLOCKING"
    NON_BLOCKING = "NON_BLOCKING"
    SUGGESTION = "SUGGESTION"


class Category(str, Enum):
    CORRECTNESS = "correctness"
    ENGINEERING_QUALITY = "engineering_quality"
    PRODUCTION_READINESS = "production_readiness"
    SECURITY = "security"


class ReviewFinding(BaseModel):
    severity: Severity
    category: Category
    title: str
    description: str
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class PRInfo(BaseModel):
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


def merge_findings(existing: List[ReviewFinding], new: List[ReviewFinding]) -> List[ReviewFinding]:
    return existing + new


class ReviewState(TypedDict):
    pr_diff: str
    pr_metadata: PRInfo
    languages: List[str]
    intent_summary: str
    findings: Annotated[List[ReviewFinding], merge_findings]
    decision: str
    confidence_score: float
    markdown_report: str
    docx_report_path: Optional[str]
    current_stage: str
    error_message: Optional[str]
