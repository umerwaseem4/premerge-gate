from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set


LANGUAGE_MAP: Dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".cs": "dotnet",
    ".csx": "dotnet",
    ".csproj": "dotnet",
    ".sln": "dotnet",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
}

SUPPORTED_LANGUAGES = {"python", "dotnet", "javascript", "typescript"}

EXCLUDED_PATTERNS = {
    ".github/",
    ".gitlab-ci",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".md",
    ".rst",
    ".txt",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    ".min.js",
    ".bundle.js",
    ".map",
    "fixtures/",
    "testdata/",
    "__snapshots__/",
}


def should_review_file(filename: str) -> bool:
    filename_lower = filename.lower()
    for pattern in EXCLUDED_PATTERNS:
        if pattern in filename_lower:
            return False
    return detect_language(filename) is not None


def filter_reviewable_files(filenames: List[str]) -> List[str]:
    return [f for f in filenames if should_review_file(f)]


def detect_language(filename: str) -> Optional[str]:
    ext = Path(filename).suffix.lower()
    return LANGUAGE_MAP.get(ext)


def detect_languages_in_files(filenames: List[str]) -> Set[str]:
    languages = set()
    for filename in filenames:
        if not should_review_file(filename):
            continue
        lang = detect_language(filename)
        if lang and lang in SUPPORTED_LANGUAGES:
            languages.add(lang)
    return languages


def get_language_display_name(language: str) -> str:
    display_names = {
        "python": "Python",
        "dotnet": ".NET (C#)",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
    }
    return display_names.get(language, language.title())
