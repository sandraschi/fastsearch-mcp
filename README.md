# FastSearch MCP

⚡ Lightning-fast file search for Claude Desktop via direct NTFS Master File Table access — no indexing, no caching, no compromises.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.13%2B-brightgreen)](https://docs.anthropic.com/claude/docs/mcp)

> **Core Principle:** FastSearch MCP follows the WizFile philosophy. Every request reads straight from the NTFS MFT. We never build background indexes, caches, or persistent file databases.

## 🚀 Why FastSearch MCP

- **Direct NTFS MFT reads** for sub-second search across millions of files.
- **Zero indexing & zero persistence** keeps startup instant and memory under 50 MB.
- **Claude-first integration** through the MCP protocol and schema-driven tools.
- **Privilege separation**: elevated C++ service handles filesystem duties, Python bridge stays in user space.
- **Graceful fallbacks** when service access is unavailable (with clear guidance to re-enable direct MFT access).

## 🏗 Architecture Overview

```
Claude Desktop
      │ JSON-RPC (stdin/stdout)
Python MCP Bridge (user privileges)
      │ Named pipe (`\\.\pipe\FastSearchMCP`)
C++ Windows Service (LocalSystem)
      │
NTFS Master File Table (live)
```

- **C++ Windows Service (`service/`)**
  - Runs as `LocalSystem`.
  - Opens NTFS volumes directly and answers search requests on demand.
  - Emits structured logging to the Windows Event Log for diagnostics.
  - No background threads, no file caches, no startup scans.

- **Python MCP Bridge (`src/fastsearch_mcp/`)**
  - Implements FastMCP 2.13 tools (`file_search`, `disk_analyzer`, `service_status`, etc.).
  - Marshals requests to the service via named pipes and reformats results for Claude.
  - Provides Python fallbacks only when MFT access is unavailable, with warnings that performance is degraded.

## 🚨 Architecture Guardrails (Non-Negotiable)

- **Never add indexing, background scanning, or persistent metadata stores.**
- **Never introduce in-memory caches of file lists or search results.**
- **Always query NTFS live and stop once `max_results` is reached.**
- **Always maintain instant startup, real-time accuracy, and minimal memory usage.**

See `docs/WIZFILE_COMPARISON.md` for the rationale.

## 📦 Installation

FastSearch MCP supports **three installation methods**:

1. **Local Installation** - Git clone for development
2. **NPX Installation** - For Cursor IDE, Windsurf IDE, Zed IDE, etc.
3. **MCPB Package** - For Claude Desktop only

**All methods require the Windows Service to be installed first** (one-time, requires UAC).

See [Installation Methods Guide](docs/INSTALLATION_METHODS.md) for detailed instructions.

### Quick Start

#### For Claude Desktop Users

1. Install service: Download `fastsearch-mcp-setup.msi` → Run as Administrator
2. Install extension: Drag `fastsearch-mcp-0.4.0.mcpb` into Claude Desktop

#### For IDE Users (Cursor, Windsurf, Zed)

1. Install service: Download `fastsearch-mcp-setup.msi` → Run as Administrator
2. Install Python package: `pip install fastsearch-mcp`
3. Configure IDE: `npx -y fastsearch-mcp`

#### For Developers

See [Local Installation](docs/INSTALLATION_METHODS.md#1-local-installation-development) for full setup.

## ▶️ Running the MCP Server Locally

```powershell
.venv\Scripts\Activate.ps1
python start_server.py
```

Add `fastsearch-mcp` to Claude Desktop’s MCP configuration (see `mcp.config.json`) to auto-launch with Claude.

## 🧪 Development Notes

- `pytest` runs the Python test suite.
- `scripts/check-repo-standards.ps1` enforces logging + doc standards.
- The service currently focuses on direct MFT access; Python fallbacks are explicitly slower and should only be used for debugging or in environments where elevation is impossible.
- Ongoing work: diagnosing an Event ID 7034 crash during service initialization on some machines (see `docs/SERVICE_DEVELOPMENT_STATUS.md`).

## 📚 Key Documentation

- `docs/TECHNICAL_ARCHITECTURE.md` – deep dive into the C++ + MCP bridge design.
- `docs/PRODUCT_REQUIREMENTS.md` – product goals and non-negotiable principles.
- `docs/SERVICE_DEVELOPMENT_STATUS.md` – current service stability & open issues.
- `docs/SERVICE_IMPROVEMENTS.md` – logging & diagnostic tooling summary.
- `docs/WIZFILE_COMPARISON.md` – why direct MFT access beats indexing.

## 🤝 Contributing

We welcome contributions that preserve the direct-MFT architecture.

1. Open an issue describing the change.
2. Confirm it does **not** add indexing, caching, or background scanning.
3. Create a feature branch and add tests where applicable.
4. Run `pytest` and the markdown linter (`scripts/lint-markdown.ps1`).
5. Submit a PR referencing the relevant docs.

## 📄 License

MIT – see [LICENSE](LICENSE).
