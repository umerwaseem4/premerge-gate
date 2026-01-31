"""Configuration management for the AI PR Reviewer."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # GitHub configuration
    github_token: str
    github_repository: str
    pr_number: int

    # OpenAI configuration
    openai_api_key: str
    openai_model: str = "gpt-4o"

    # Derived properties
    @property
    def repo_owner(self) -> str:
        """Extract repository owner from GITHUB_REPOSITORY."""
        return self.github_repository.split("/")[0]

    @property
    def repo_name(self) -> str:
        """Extract repository name from GITHUB_REPOSITORY."""
        return self.github_repository.split("/")[1]


def load_config() -> Config:
    """Load configuration from environment variables.

    Raises:
        ValueError: If required environment variables are missing.
    """
    load_dotenv()

    def get_required(key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Missing required environment variable: {key}")
        return value

    def get_optional(key: str, default: str) -> str:
        return os.getenv(key, default)

    return Config(
        github_token=get_required("GITHUB_TOKEN"),
        github_repository=get_required("GITHUB_REPOSITORY"),
        pr_number=int(get_required("PR_NUMBER")),
        openai_api_key=get_required("OPENAI_API_KEY"),
        openai_model=get_optional("OPENAI_MODEL", "gpt-4o"),
    )
