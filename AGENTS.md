# FastSearch MCP — Agent Context

## Identity
FastSearch MCP provides lightning-fast file search on Windows via direct NTFS Master File Table (MFT) access. No indexing, no caching.

## Architecture
- **C++ Windows service** (`service/`) runs as LocalSystem or interactive `--standalone` console mode, reading MFT directly via named pipe `\\.\pipe\FastSearchMCP`
- **Python bridge** (`src/fastsearch_mcp/`) FastMCP 3.2 server with REST API bridge (`api_bridge.py`)
- **Web dashboard** (`web_sota/`) SOTA React UI on port 10844 with Dedicated Search page (`/search`), API bridge on 10845

## Key Files
- `pyproject.toml` — Python deps, fastmcp>=3.2.0,<4
- `src/fastsearch_mcp/mcp_instance.py` — FastMCP instance
- `src/fastsearch_mcp/server.py` — FastAPI + FastMCP server
- `src/fastsearch_mcp/api_bridge.py` — Direct REST API endpoints (`/api/search`, `/api/service/*`, `/api/file`)
- `src/fastsearch_mcp/transport.py` — STDIO/HTTP/SSE transport + --agentic flag
- `src/fastsearch_mcp/prompts.py` — @mcp.prompt() templates
- `src/fastsearch_mcp/skills.py` — @mcp.skill() definitions
- `src/fastsearch_mcp/pipe_client.py` — Named pipe connection client to C++ service
- `service/src/mft_search.cpp` — C++ MFT parsing engine
- `service/src/fastsearch_service.cpp` — C++ service and standalone interactive server
- `service/build/bin/Release/FastSearchServiceNew.exe` — Built release executable
- `web_sota/src/pages/search.tsx` — Dedicated SOTA Search page UI

## Version
0.5.0 — FastMCP 3.2 with CodeMode, prompts, skills, direct REST API bridge, and dedicated SOTA search page

## Ports
- 10844 — Web dashboard frontend (`web_sota`)
- 10845 — FastAPI + MCP HTTP backend

## Commands & Modes
- Python backend: `uv run python run_server.py` or `just run-api`
- Webapp frontend: `cd web_sota && npm run dev` or `just run-web`
- C++ Service standalone mode: `FastSearchServiceNew.exe --standalone`
- C++ Service management: `FastSearchServiceNew.exe install|start|stop|uninstall` (supports both standard and `--` prefix)
- C++ service build: `cmake --build service/build --config Release` or `just build-service`

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md
