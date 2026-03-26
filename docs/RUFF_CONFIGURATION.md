# Ruff Linting and Formatting Configuration

**Status:** ✅ Active and configured  
**Location:** Configuration in `pyproject.toml`  
**Version:** Ruff 0.1.6+ (via dev dependencies)

---

## Overview

Ruff is used for both **linting** and **formatting** in this project, replacing Black, isort, and flake8.

---

## Configuration

The ruff configuration is in `pyproject.toml` under:
- `[tool.ruff]` - General settings
- `[tool.ruff.format]` - Formatting options
- `[tool.ruff.lint]` - Linting rules

### Selected Linting Rules

We enable comprehensive linting rules:

- **E** - pycodestyle errors
- **W** - pycodestyle warnings  
- **F** - pyflakes
- **I** - isort (import sorting)
- **B** - flake8-bugbear
- **C4** - flake8-comprehensions
- **UP** - pyupgrade

### Formatting Configuration

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

**Line length:** 100 characters (enforced by Ruff)

### Per-File Ignores

Some files have legitimate reasons to ignore certain rules:

- **E402** (Module import not at top) - Required for FastMCP 2.13+ pattern
- **F401** (Unused imports) - Side-effect imports for tool registration
- **C901** (Too complex) - Some functions legitimately need complexity

See `pyproject.toml` for specific file-level ignores.

---

## Usage

### Check for Issues

```powershell
# Check all files
uv run ruff check .

# Check specific directory
uv run ruff check src/ tests/

# Check with auto-fix
uv run ruff check . --fix
```

### Format Code

```powershell
# Format all files
uv run ruff format .

# Format specific directory
uv run ruff format src/ tests/

# Check formatting without changing files
uv run ruff format --check .
```

### Pre-Commit Hooks

Ruff is configured in `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.15
  hooks:
    - id: ruff
      args: [--fix, --exit-non-zero-on-fix]
    - id: ruff-format
```

**Install hooks:**
```powershell
pip install pre-commit
pre-commit install
```

---

## CI/CD Integration

Ruff runs automatically in CI (`.github/workflows/ci.yml`):

1. **Linting check:** `ruff check src/ tests/`
2. **Formatting check:** `ruff format --check src/ tests/`

Both must pass for CI to succeed.

---

## Development Workflow

### Before Committing

1. **Run linting:**
   ```powershell
   uv run ruff check .
   ```

2. **Auto-fix issues:**
   ```powershell
   uv run ruff check . --fix
   ```

3. **Format code:**
   ```powershell
   uv run ruff format .
   ```

### After Adding/Modifying Code

- **ALWAYS run ruff check** after tool addition/modification
- **ALWAYS run ruff format** after linting passes
- **ZERO errors required** before committing

---

## Common Issues and Solutions

### Unused Imports (F401)

**Fix:**
```powershell
uv run ruff check . --fix
# Or manually remove unused imports
```

### Import Sorting (I001)

**Fix:**
```powershell
uv run ruff check . --fix
# Automatically sorts imports
```

### Line Too Long (E501)

**Fix:**
- Break long lines
- Ruff will format automatically if possible
- Line length limit: 100 characters

### Blank Line Whitespace (W293)

**Fix:**
```powershell
uv run ruff check . --fix
# Automatically removes trailing whitespace
```

---

## Why Ruff?

**Benefits:**
- ⚡ **Fast** - 10-100x faster than Black + isort + flake8
- 🔧 **All-in-one** - Linting + formatting in single tool
- 🎯 **Compatible** - Drop-in replacement for Black/isort
- 📦 **Single dependency** - One tool instead of three

**Replaces:**
- ❌ Black (formatting)
- ❌ isort (import sorting)
- ❌ flake8 (linting)

---

## References

- **Ruff Documentation:** https://docs.astral.sh/ruff/
- **Configuration:** `pyproject.toml` `[tool.ruff]` section
- **Pre-commit:** `.pre-commit-config.yaml`
- **CI Workflow:** `.github/workflows/ci.yml`

---

*Last Updated: 2025-01-15*

