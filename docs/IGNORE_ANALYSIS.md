# Ruff Ignore Analysis

**Date:** November 15, 2025

## Current Ignores

### B008 - Function calls in argument defaults

**Instance:** `return_type: type = type(None)` in `base.py:162`

**Analysis:**
- `type(None)` is a builtin that returns the same immutable object
- Technically safe, but violates the rule
- **Easy fix:** Use `NoneType` or module-level constant

**Recommendation:** ✅ **FIX IT** - Easy to fix, no reason to ignore

### C901 - Too complex

**Instances Found:** 11 functions

1. `get_status` in `mcp_server.py` (complexity 19)
2. `_search_sync` in `file_search.py` (complexity 24)
3. `scan_directory` in `integrity_checker.py` (complexity 14)
4. `execute` in `integrity_checker.py` (complexity 14)
5. `execute` in `integrity_checker.py` (complexity 11)
6. `execute` in `service_manager.py` (complexity 26)
7. `find_files` in `file_utils.py` (complexity 12)
8. `test_mft_search` in `test_mft_search.py` (complexity 13)
9. `read_service_event_logs` in `test_service_with_logs.py` (complexity 12)
10. `test_service_with_logs` in `test_service_with_logs.py` (complexity 14)

**Analysis:**
- Many are in test files (can ignore per-file)
- Some are legitimately complex business logic
- Some could be refactored

**Recommendation:** ⚠️ **PARTIAL IGNORE** - Ignore in test files, fix or document in source

## Recommendations

### Option 1: Fix Both (Best Practice)
1. Fix B008 by using `NoneType` or module constant
2. Refactor complex functions or use per-file ignores for tests

### Option 2: Keep Ignores (Pragmatic)
1. Keep B008 ignore (only 1 instance, safe)
2. Keep C901 ignore (many instances, some legitimate)

### Option 3: Selective Ignores (Balanced)
1. Fix B008
2. Remove C901 from global ignore
3. Add per-file ignores for test files
4. Fix or document complex source functions

## Proposed Fixes

### Fix B008

```python
# Current (violates B008):
return_type: type = type(None)

# Option 1: Use NoneType
from types import NoneType
return_type: type = NoneType

# Option 2: Module-level constant
_NONE_TYPE = type(None)
return_type: type = _NONE_TYPE
```

### Fix C901

For test files, add to `pyproject.toml`:
```toml
[tool.ruff.lint.per-file-ignores]
"test_*.py" = ["C901"]
"*_test.py" = ["C901"]
```

For source files, either:
- Refactor to reduce complexity
- Add `# noqa: C901` with justification comment

