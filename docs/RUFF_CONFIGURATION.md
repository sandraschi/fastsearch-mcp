# Ruff Linting Configuration

**Date:** November 15, 2025  
**Status:** Updated to new format

## Configuration

The ruff configuration is in `pyproject.toml` under `[tool.ruff.lint]`.

### Selected Rules

We enable comprehensive linting rules:

- **E** - pycodestyle errors
- **W** - pycodestyle warnings  
- **F** - pyflakes
- **I** - isort (import sorting)
- **B** - flake8-bugbear
- **C4** - flake8-comprehensions
- **UP** - pyupgrade

### Ignored Rules

We ignore only 2 rules with good justification:

#### ~~E501 - Line too long~~ (REMOVED)
**Previous Reason:** Handled by Black formatter  
**Status:** ✅ **REMOVED** - Ruff now handles formatting and line length checking

#### B008 - Function calls in argument defaults
**Reason:** Only one instance: `type(None)` in `base.py` line 162  
**Instance:** `return_type: type = type(None)`  
**Status:** ✅ Safe - `type(None)` is a builtin, not a mutable call  
**Note:** This is a false positive - `type(None)` is safe to use in defaults

#### C901 - Too complex
**Reason:** One function legitimately needs complexity  
**Instance:** `get_status()` in `mcp_server.py` (complexity 19)  
**Status:** ⚠️ Could be refactored, but function handles multiple service states  
**Note:** This function checks service installation, state, registry, and provides suggestions

## Current Issues

**Total:** 222 errors found  
**Fixable:** 210 (95%)  
**Unfixable:** 12 (5%)

### Breakdown:
- 172 W293 - Blank line whitespace (fixable)
- 16 I001 - Unsorted imports (fixable)
- 14 F401 - Unused imports (manual fix)
- 8 F541 - F-string missing placeholders (fixable)
- 6 E722 - Bare except (manual fix)
- 3 F841 - Unused variables (manual fix)
- 2 E402 - Module import not at top (manual fix)
- 1 UP015 - Redundant open modes (fixable)

## Formatting Configuration

Ruff is now used for both linting and formatting (replacing Black):

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

**Line length:** 100 characters (enforced by Ruff, E501 is checked)

## Recommendations

### Should We Remove Any Ignores?

**B008:** Keep - `type(None)` is safe  
**C901:** Consider refactoring `get_status()` to reduce complexity, but keep ignore for now

### Should We Add More Ignores?

**No** - The current ignore list is minimal and justified. Most issues are fixable.

## Auto-Fix

Run `ruff check --fix .` to automatically fix 210 issues (95% of all issues).

## Migration to New Format

✅ **Updated:** Configuration moved from top-level `[tool.ruff]` to `[tool.ruff.lint]` section to match Ruff's new format and eliminate deprecation warnings.

