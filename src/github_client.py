"""GitHub API client for PR operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional

from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository

from src.config import Config


@dataclass
class PRMetadata:
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


@dataclass
class FileDiff:
    filename: str
    status: str
    additions: int
    deletions: int
    patch: Optional[str]


class GitHubClient:
    STATUS_CONTEXT = "AI Staff Review"

    def __init__(self, config: Config):
        self.config = config
        self.github = Github(config.github_token)
        self._repo: Optional[Repository] = None
        self._pr: Optional[PullRequest] = None

    @property
    def repo(self) -> Repository:
        if self._repo is None:
            self._repo = self.github.get_repo(self.config.github_repository)
        return self._repo

    @property
    def pr(self) -> PullRequest:
        if self._pr is None:
            self._pr = self.repo.get_pull(self.config.pr_number)
        return self._pr

    def get_pr_metadata(self) -> PRMetadata:
        pr = self.pr
        files = list(pr.get_files())
        return PRMetadata(
            number=pr.number,
            title=pr.title,
            description=pr.body,
            author=pr.user.login,
            base_branch=pr.base.ref,
            head_branch=pr.head.ref,
            files_changed=[f.filename for f in files],
            additions=pr.additions,
            deletions=pr.deletions,
            url=pr.html_url,
        )

    def get_pr_diff(self) -> List[FileDiff]:
        files = self.pr.get_files()
        diffs = []
        for file in files:
            diffs.append(
                FileDiff(
                    filename=file.filename,
                    status=file.status,
                    additions=file.additions,
                    deletions=file.deletions,
                    patch=file.patch,
                )
            )
        return diffs

    def get_full_diff_text(self) -> str:
        diffs = self.get_pr_diff()
        parts = []
        for diff in diffs:
            if diff.patch:
                parts.append(f"=== {diff.filename} ({diff.status}) ===")
                parts.append(diff.patch)
                parts.append("")
        return "\n".join(parts)

    def set_status(
        self,
        state: Literal["pending", "success", "failure", "error"],
        description: str,
        target_url: Optional[str] = None,
    ) -> None:
        commit = self.repo.get_commit(self.pr.head.sha)
        commit.create_status(
            state=state,
            target_url=target_url or "",
            description=description[:140],
            context=self.STATUS_CONTEXT,
        )

    def post_comment(self, body: str) -> int:
        comment = self.pr.create_issue_comment(body)
        return comment.id

    def update_comment(self, comment_id: int, body: str) -> None:
        comment = self.pr.get_issue_comment(comment_id)
        comment.edit(body)

    def find_existing_review_comment(self) -> Optional[int]:
        comments = self.pr.get_issue_comments()
        for comment in comments:
            if comment.body.startswith("## AI Staff Review"):
                return comment.id
        return None

    def get_workflow_run_url(self) -> Optional[str]:
        import os
        run_id = os.getenv("GITHUB_RUN_ID")
        if run_id:
            return f"https://github.com/{self.config.github_repository}/actions/runs/{run_id}"
        return None
