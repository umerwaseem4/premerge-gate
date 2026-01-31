"""Language-specific review criteria."""

from __future__ import annotations

from typing import List


PYTHON_CRITERIA = """
## Python-Specific Review Criteria

### Correctness
- Missing None checks before method calls
- Mutable default arguments (e.g., def foo(x=[]))
- Improper exception handling with generic exception types
- Potential KeyError when accessing dicts without .get()
- Incorrect use of is vs == for value comparisons

### Engineering Quality
- Missing type hints on public functions
- SQLAlchemy N+1 query patterns
- Missing pagination for list/query operations
- Blocking I/O in async functions
- Missing input validation

### Production Readiness
- Hardcoded secrets or API keys
- Missing logging
- Missing timeout parameters on HTTP requests
- Environment variables accessed without defaults
- Missing error handling for external service calls
"""

DOTNET_CRITERIA = """
## .NET (C#) Specific Review Criteria

### Correctness
- Null reference exceptions (missing null checks)
- Improper async/await usage (missing await, async void)
- IDisposable not properly disposed (missing using statements)
- String comparison without StringComparison parameter
- Collection modification during enumeration

### Engineering Quality
- Entity Framework N+1 queries (not using .Include())
- Missing pagination on IQueryable
- Synchronous database calls instead of async
- Missing input validation
- Not using ILogger<T> for logging

### Production Readiness
- Secrets in appsettings.json
- Missing HttpClient timeout configuration
- Hardcoded config values
- Missing structured logging
- Catching Exception instead of specific types
"""

JAVASCRIPT_CRITERIA = """
## JavaScript/TypeScript Specific Review Criteria

### Correctness
- Missing null/undefined checks
- Not handling Promise rejections
- Using == instead of ===
- Race conditions in async state updates
- Incorrect this binding in callbacks

### Engineering Quality
- Missing input validation
- N+1 queries (not using include)
- Missing pagination parameters
- Not using TypeScript strict mode
- Unbounded array operations

### Production Readiness
- console.log instead of proper logging
- Hardcoded API keys or secrets
- Missing process.env usage for configuration
- No timeout on fetch calls
- Missing error boundaries in React
"""

TYPESCRIPT_CRITERIA = JAVASCRIPT_CRITERIA


def get_language_criteria(language: str) -> str:
    criteria_map = {
        "python": PYTHON_CRITERIA,
        "dotnet": DOTNET_CRITERIA,
        "javascript": JAVASCRIPT_CRITERIA,
        "typescript": TYPESCRIPT_CRITERIA,
    }
    return criteria_map.get(language, "")


def get_combined_criteria(languages: List[str]) -> str:
    criteria_parts = []
    for lang in languages:
        criteria = get_language_criteria(lang)
        if criteria:
            criteria_parts.append(criteria)

    if not criteria_parts:
        return "No specific language criteria available. Apply general code review best practices."

    return "\n\n---\n\n".join(criteria_parts)
