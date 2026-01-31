"""Language detection for PR files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set


# Mapping of file extensions to language identifiers
LANGUAGE_MAP: Dict[str, str] = {
    # Python
    ".py": "python",
    ".pyi": "python",
    # .NET / C#
    ".cs": "dotnet",
    ".csx": "dotnet",
    ".csproj": "dotnet",
    ".sln": "dotnet",
    # JavaScript
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    # TypeScript
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
}

# Supported languages for review
SUPPORTED_LANGUAGES = {"python", "dotnet", "javascript", "typescript"}


def detect_language(filename: str) -> Optional[str]:
    """Detect the programming language from a filename.

    Args:
        filename: The name or path of the file.

    Returns:
        The language identifier, or None if not recognized.
    """
    ext = Path(filename).suffix.lower()
    return LANGUAGE_MAP.get(ext)


def detect_languages_in_files(filenames: List[str]) -> Set[str]:
    """Detect all programming languages present in a list of files.

    Args:
        filenames: List of filenames or paths.

    Returns:
        Set of language identifiers found.
    """
    languages = set()
    for filename in filenames:
        lang = detect_language(filename)
        if lang and lang in SUPPORTED_LANGUAGES:
            languages.add(lang)
    return languages


def get_language_display_name(language: str) -> str:
    """Get a human-readable display name for a language.

    Args:
        language: The language identifier.

    Returns:
        Human-readable language name.
    """
    display_names = {
        "python": "Python",
        "dotnet": ".NET (C#)",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
    }
    return display_names.get(language, language.title())
