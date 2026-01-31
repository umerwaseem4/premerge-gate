"""Configuration management."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    github_token: str
    github_repository: str
    pr_number: int
    openai_api_key: str
    openai_model: str = "gpt-4o"

    @property
    def repo_owner(self) -> str:
        return self.github_repository.split("/")[0]

    @property
    def repo_name(self) -> str:
        return self.github_repository.split("/")[1]


def load_config() -> Config:
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
