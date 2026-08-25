# FastSearch MCP

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

  
> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

Lightning-fast file search via direct NTFS Master File Table access — zero indexing, zero caching. FastMCP 3.2 with CodeMode, prompts, and skills.

> **Core Principle:** FastSearch MCP follows the WizFile philosophy. Every request reads straight from the NTFS MFT. We never build background indexes, caches, or persistent file databases.

## Quick Start

```powershell
git clone https://github.com/sandraschi/fastsearch-mcp
cd fastsearch-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:

##  Why FastSearch MCP

- **Direct NTFS MFT reads** for sub-second search across millions of files.
- **Zero indexing & zero persistence** keeps startup instant and memory under 50 MB.
- **FastMCP 3.2**: sampling, CodeMode (`--agentic`), `@mcp.prompt()`, `@mcp.skill()`
- **Privilege separation**: elevated C++ service handles filesystem duties, Python bridge stays in user space.
- **Fast service checks** - <1ms overhead per search (optimized from 5 seconds).
- **Clear error messages** - Actionable guidance when service is unavailable.

##  Architecture Overview

```
Claude Desktop
       JSON-RPC (stdin/stdout)
Python MCP Bridge (user privileges)
       Named pipe (`\\.\pipe\FastSearchMCP`)
C++ Windows Service (LocalSystem)
      
NTFS Master File Table (live)
```

- **C++ Windows Service (`service/`)**
  - Runs as `LocalSystem`.
  - Opens NTFS volumes directly and answers search requests on demand.
  - Emits structured logging to the Windows Event Log for diagnostics.
  - No background threads, no file caches, no startup scans.

- **Python MCP Bridge (`src/fastsearch_mcp/`)**
  - FastMCP 3.2: **sampling** via `ctx.sampling()`, **CodeMode** agentic discovery (`--agentic`), **prompts** (`@mcp.prompt()`), and **skills** (`@mcp.skill()`).
  - Implements 18 FastMCP 3.2 tools (`fastsearch_search`, `disk_analyzer`, `service_status`, etc.).
  - Marshals requests to the service via named pipes and reformats results for Claude.
  - Fast service availability checks (<1ms) before each search.
  - Clear error messages when service is unavailable (no silent fallbacks).

##  Architecture Guardrails (Non-Negotiable)

- **Never add indexing, background scanning, or persistent metadata stores.**
- **Never introduce in-memory caches of file lists or search results.**
- **Always query NTFS live and stop once `max_results` is reached.**
- **Always maintain instant startup, real-time accuracy, and minimal memory usage.**

See `docs/WIZFILE_COMPARISON.md` for the rationale.

## FastMCP 3.2: Sampling, CodeMode, Prompts, Skills, Gateway

- **Sampling**: Tools can request LLM completions from the client via `ctx.sampling()` (FastMCP 3.2 `Context` injection). No server-side configuration needed — the client provides the sampling handler.
- **CodeMode agentic discovery**: Run with `--agentic` flag or `MCP_AGENTIC=true` to collapse all tools into discovery + execute meta-tools, using FastMCP 3.2's `CodeMode().attach(mcp)` transform.
- **Prompts**: 3 built-in `@mcp.prompt()` templates: file search guide, disk analysis guide, service troubleshooting. Auto-registered at import time.
- **Skills**: 3 composable `@mcp.skill()` workflows: find recently modified files, cleanup disk space, forensic file audit.
- **Unified gateway**: Run as a proxy that aggregates or bridges other MCP servers (transport bridging, session isolation, forwards sampling/elicitation/logging/progress):
  ```bash
  # Single backend
  set FASTSEARCH_GATEWAY_URL=http://127.0.0.1:8000/mcp
  uv run python -m fastsearch_mcp.gateway

  # Or use the console script
  fastsearch-gateway
  ```
  Optional: `FASTSEARCH_GATEWAY_CONFIG` for multi-server JSON config; `MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT` to run the gateway over HTTP.

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx fastsearch-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "fastsearch-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/fastsearch-mcp", "run", "fastsearch-mcp"]
  }
}
```
### Quick Start

#### For IDE Users (Cursor, Windsurf, Zed)  **Recommended**

1. Install service: Download `fastsearch-mcp-setup.msi`  Run as Administrator
2. Install Python package: `pip install fastsearch-mcp`
3. Configure IDE: `npx -y fastsearch-mcp`

#### For Claude Desktop Users

1. Install service: Download `fastsearch-mcp-setup.msi`  Run as Administrator
2. Install extension: Drag `fastsearch-mcp-0.4.0.mcpb` into Claude Desktop
   - **Note**: MCPB format is Claude Desktop specific. The "drag-and-drop into settings UI" UX is unconventional.
   - **Benefit**: MCPB includes prompt templates (system prompts, user guides) that help Claude understand capabilities.
   - **Alternative**: Use NPX installation above for standard MCP config (works with Claude Desktop too).
   - **See**: [`docs/MCPB_STATUS.md`](docs/MCPB_STATUS.md) for detailed explanation of MCPB limitations and prompt template alternatives.

#### For Developers

See [Local Installation](docs/INSTALLATION_METHODS.md#1-local-installation-development) for full setup.

##  Running the MCP Server Locally

```powershell
.venv\Scripts\Activate.ps1
python scripts/start_server.py
```

Add `fastsearch-mcp` to Claude Desktop's MCP configuration (see `mcp.config.json`) to auto-launch with Claude.

##  Development Notes

- `pytest` runs the Python test suite (18/18 tests passing). With the FastSearch service running (Windows), `pytest tests/test_live_pipe.py -v` runs live pipe + search integration tests.
- **Tests page:** In the webapp, open `/tests` to run the same live tests from the UI.
- `scripts/check-repo-standards.ps1` enforces logging + doc standards.
- **Search functionality fully operational** - All search tools working with direct NTFS MFT access.
- **Service running** - FastSearch Windows service operational and responding to requests.
- **Performance optimized** - Service checks optimized to <1ms (from 5 seconds).

See `docs/RECENT_IMPROVEMENTS.md` for details on recent improvements.

##  Key Documentation

- `docs/RECENT_IMPROVEMENTS.md`  **NEW** - Recent improvements and search functionality status.
- `docs/STATUS_REPORT.md`  Current project status and what's working.
- `docs/TECHNICAL_ARCHITECTURE.md`  deep dive into the C++ + MCP bridge design.
- `docs/PRODUCT_REQUIREMENTS.md`  product goals and non-negotiable principles.
- `docs/SERVICE_AVAILABILITY_CHECKS.md`  How service availability is checked and error handling.
- `docs/PIPE_CONNECTION_TROUBLESHOOTING.md`  Pipe not found (error 2): diagnosis, Event Log, fixes.
- `docs/STATUS_NOTE_MEMOPS.md`  Short ops status note for pipe connect failures.
- `docs/WIZFILE_COMPARISON.md`  why direct MFT access beats indexing.

##  Contributing

We welcome contributions that preserve the direct-MFT architecture.

1. Open an issue describing the change.
2. Confirm it does **not** add indexing, caching, or background scanning.
3. Create a feature branch and add tests where applicable.
4. Run `pytest` and the markdown linter (`scripts/lint-markdown.ps1`).
5. Submit a PR referencing the relevant docs.


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.
## 🌐 Webapp Dashboard & Dedicated Search Page

This MCP server includes a free, premium web interface for file search, monitoring, and service control.
By default, the web dashboard runs on port **10844** with REST API bridge on port **10845**.

**Features & Pages:**
- **Dedicated Search Page (`/search`)**: SOTA file search UI with live service status badge, instant drive shortcuts (`C:\`, `D:\`), category filters (Code, Docs, Images, Media, Archives, Apps), interactive data table with sorting/pagination, file preview drawer (text, hex, image), JSON/CSV export, and query history.
- **System Insight (`/`)**: Real-time service operational status and health metrics.
- **NTFS Search Service (`/service`)**: Start, stop, restart, repair, or monitor the C++ named pipe service.
- **Tests (`/tests`)**: Live integration test suite verifying named pipe connections and queries.
- **Tools, Actions, AI Assistant, System Logs, Settings**.

To start the webapp:
1. `uv run python run_server.py` (API bridge on port 10845)
2. `cd web_sota && npm run dev` (Frontend on port 10844)
3. Open `http://localhost:10844/search` in your browser.

##  License

MIT — see [LICENSE](LICENSE).
