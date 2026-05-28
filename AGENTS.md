# FastSearch MCP — Agent Context

## Identity
FastSearch MCP provides lightning-fast file search on Windows via direct NTFS Master File Table (MFT) access. No indexing, no caching.

## Architecture
- **C++ Windows service** (`service/`) runs as LocalSystem, reads MFT directly via named pipe
- **Python bridge** (`src/fastsearch_mcp/`) FastMCP 3.2 server with 18 tools
- **Web dashboard** (`web_sota/`) on port 10844, API on 10845

## Key Files
- `pyproject.toml` — Python deps, fastmcp>=3.2.0,<4
- `src/fastsearch_mcp/mcp_instance.py` — FastMCP instance
- `src/fastsearch_mcp/server.py` — FastAPI + FastMCP server
- `src/fastsearch_mcp/transport.py` — STDIO/HTTP/SSE transport + --agentic flag
- `src/fastsearch_mcp/prompts.py` — @mcp.prompt() templates
- `src/fastsearch_mcp/skills.py` — @mcp.skill() definitions
- `src/fastsearch_mcp/pipe_client.py` — Named pipe to C++ service
- `service/src/mft_search.cpp` — C++ MFT parsing
- `service/src/fastsearch_service.cpp` — C++ named pipe service
- `service/build/` — CMake build output

## Version
0.5.0 — FastMCP 3.2 with CodeMode, prompts, skills

## Ports
- 10844 — Web dashboard frontend
- 10845 — FastAPI + MCP HTTP backend

## Build
- Python: `uv sync`, `python -m fastsearch_mcp`
- C++ service: `cmake --build service/build --config Release`
- Run with agentic mode: `python -m fastsearch_mcp --agentic`
- Justfile: `just` (dashboard), `just lint`, `just fix`, `just check-sec`

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md
