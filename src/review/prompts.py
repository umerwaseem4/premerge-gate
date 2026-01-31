"""Language-specific review prompts and criteria."""

from __future__ import annotations

from typing import List

# Python-specific review criteria
PYTHON_CRITERIA = """
## Python-Specific Review Criteria

### Correctness
- Check for missing `None` checks before method calls
- Look for mutable default arguments (e.g., `def foo(x=[])`)
- Verify proper exception handling with specific exception types
- Check for potential `KeyError` when accessing dicts without `.get()`
- Look for incorrect use of `is` vs `==` for value comparisons

### Engineering Quality
- Missing type hints on public functions
- SQLAlchemy N+1 query patterns (accessing relationships in loops)
- Missing pagination for list/query operations
- Blocking I/O in async functions
- Missing input validation with Pydantic or type checking

### Production Readiness
- Hardcoded secrets or API keys
- Missing logging with the `logging` module
- Missing timeout parameters on HTTP requests (requests/httpx)
- Environment variables accessed without defaults
- Missing error handling for external service calls
"""

DOTNET_CRITERIA = """
## .NET (C#) Specific Review Criteria

### Correctness
- Null reference exceptions (missing null checks before dereferencing)
- Improper `async`/`await` usage (missing await, async void)
- `IDisposable` not properly disposed (missing `using` statements)
- String comparison without `StringComparison` parameter
- Collection modification during enumeration

### Engineering Quality
- Entity Framework N+1 queries (not using `.Include()`)
- Missing pagination on `IQueryable` (calling `.ToList()` on unbounded queries)
- Synchronous database calls instead of async
- Missing input validation (no `[Required]` or FluentValidation)
- Not using `ILogger<T>` for dependency-injected logging

### Production Readiness
- Secrets in `appsettings.json` without Azure Key Vault / Secret Manager
- Missing `HttpClient` timeout configuration
- No `IConfiguration` usage (hardcoded config values)
- Missing structured logging / Application Insights
- Catching `Exception` instead of specific exception types
"""

JAVASCRIPT_CRITERIA = """
## JavaScript/TypeScript Specific Review Criteria

### Correctness
- Missing null/undefined checks (`?.` optional chaining not used)
- Not handling Promise rejections (missing `.catch()` or try/catch)
- Using `==` instead of `===` for comparisons
- Race conditions in async state updates
- Incorrect `this` binding in callbacks

### Engineering Quality
- Missing Zod/Yup/class-validator input validation
- Prisma/Sequelize N+1 queries (not using `include`)
- Missing pagination parameters on list queries
- Not using TypeScript strict mode
- Unbounded array operations (`.map()` on unsanitized input)

### Production Readiness
- `console.log` instead of proper logging (pino, winston)
- Hardcoded API keys or secrets
- Missing `process.env` usage for configuration
- No timeout on `fetch` calls
- Missing error boundaries in React components
"""

TYPESCRIPT_CRITERIA = JAVASCRIPT_CRITERIA  # Same criteria apply


def get_language_criteria(language: str) -> str:
    """Get the review criteria for a specific language.

    Args:
        language: The language identifier.

    Returns:
        The language-specific review criteria as a markdown string.
    """
    criteria_map = {
        "python": PYTHON_CRITERIA,
        "dotnet": DOTNET_CRITERIA,
        "javascript": JAVASCRIPT_CRITERIA,
        "typescript": TYPESCRIPT_CRITERIA,
    }
    return criteria_map.get(language, "")


def get_combined_criteria(languages: List[str]) -> str:
    """Get combined review criteria for multiple languages.

    Args:
        languages: List of language identifiers.

    Returns:
        Combined review criteria as a markdown string.
    """
    criteria_parts = []
    for lang in languages:
        criteria = get_language_criteria(lang)
        if criteria:
            criteria_parts.append(criteria)

    if not criteria_parts:
        return "No specific language criteria available. Apply general code review best practices."

    return "\n\n---\n\n".join(criteria_parts)
