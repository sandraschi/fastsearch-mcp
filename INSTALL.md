# Installation

## 🚀 Quick Start (recommended)

```powershell
# Install just if you don't have it
# Install just if you don't have it
winget install Casey.Just    # Windows
# scoop install just          # Windows (alternative)
# brew install just           # macOS
# sudo apt install just       # Debian/Ubuntu
# cargo install just          # Linux (Rust)

git clone https://github.com/sandraschi/fastsearch-mcp
cd fastsearch-mcp
just onboard
```

`just onboard` automates the complete onboarding sequence: prompts for Administrator elevation **ONCE** via UAC to register & start the `FastSearchMCP` background Windows Service under `LocalSystem`, then automatically runs unprivileged Win32 Named Pipe IPC diagnostics (`\\.\pipe\FastSearchMCP`). Once complete, all user tools (Claude Desktop, Web UI, Python MCP) query NTFS MFT records with **zero UAC prompts**.

Run `just` to open the interactive dashboard showing all available commands:

```powershell
just bootstrap   # install all dependencies
just dev         # start MCP server & frontend dev environment
just serve       # start production server
```

> **Why not `pip install`?** MCP servers bundle webapps, configs, project scaffolding, and tooling that a flat Python package can't deliver. PyPI offers no safety advantage — it doesn't audit packages either. `just` gives you the complete, ready-to-run stack.

---

## 🐌 Traditional Setup

If you prefer not to use `just`:

1. Install [Python 3.13+](https://python.org) and [uv](https://docs.astral.sh/uv/)
2. Clone and enter the repo:
   ```powershell
   git clone https://github.com/sandraschi/fastsearch-mcp
   cd fastsearch-mcp
   ```
3. Install dependencies:
   ```powershell
   uv sync --all-extras
   ```
4. Start the server:
   ```powershell
   # stdio mode (for MCP clients like Claude Desktop)
   uv run python -m fastsearch_mcp.server

   # HTTP mode (for web dashboard)
   uv run uvicorn fastsearch_mcp.server:app --port 10845
   ```
5. Open `http://localhost:10845` or the frontend URL.

---

## ❓ Troubleshooting

| Issue | Fix |
|---|---|
| `just` not found | Install via `winget install Casey.Just`, `scoop install just`, or `brew install just` |
| Port conflict | Run `just kill-all` to clear fleet ports (10700–11000) |
| Dependencies out of sync | `uv sync --all-extras` |
| Something else | [Open a GitHub issue](https://github.com/sandraschi/fastsearch-mcp/issues) |

---

*See the main [README](README.md) for feature overview and documentation.*
