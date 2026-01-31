"""Tests for language detection."""

import pytest

from src.language_detector import (
    detect_language,
    detect_languages_in_files,
    get_language_display_name,
)


class TestDetectLanguage:
    """Tests for detect_language function."""

    def test_python_files(self):
        assert detect_language("main.py") == "python"
        assert detect_language("src/utils.py") == "python"
        assert detect_language("types.pyi") == "python"

    def test_dotnet_files(self):
        assert detect_language("Program.cs") == "dotnet"
        assert detect_language("src/Models/User.cs") == "dotnet"
        assert detect_language("MyProject.csproj") == "dotnet"

    def test_javascript_files(self):
        assert detect_language("index.js") == "javascript"
        assert detect_language("App.jsx") == "javascript"
        assert detect_language("server.mjs") == "javascript"

    def test_typescript_files(self):
        assert detect_language("index.ts") == "typescript"
        assert detect_language("App.tsx") == "typescript"
        assert detect_language("types.mts") == "typescript"

    def test_unknown_files(self):
        assert detect_language("README.md") is None
        assert detect_language("Dockerfile") is None
        assert detect_language("config.yaml") is None


class TestDetectLanguagesInFiles:
    """Tests for detect_languages_in_files function."""

    def test_single_language(self):
        files = ["main.py", "utils.py", "tests.py"]
        assert detect_languages_in_files(files) == {"python"}

    def test_multiple_languages(self):
        files = ["main.py", "Program.cs", "index.ts"]
        result = detect_languages_in_files(files)
        assert result == {"python", "dotnet", "typescript"}

    def test_empty_list(self):
        assert detect_languages_in_files([]) == set()

    def test_no_supported_languages(self):
        files = ["README.md", "Dockerfile", ".gitignore"]
        assert detect_languages_in_files(files) == set()


class TestGetLanguageDisplayName:
    """Tests for get_language_display_name function."""

    def test_known_languages(self):
        assert get_language_display_name("python") == "Python"
        assert get_language_display_name("dotnet") == ".NET (C#)"
        assert get_language_display_name("javascript") == "JavaScript"
        assert get_language_display_name("typescript") == "TypeScript"

    def test_unknown_language(self):
        assert get_language_display_name("rust") == "Rust"
        assert get_language_display_name("go") == "Go"
