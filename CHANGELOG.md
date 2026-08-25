# Changelog

All notable changes to FastSearch MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] — 2026-08-25

### Added
- **Dedicated SOTA Search Page (`/search`)**: Built new dedicated file search page in `web_sota` featuring live service health status badge with one-click service start, instant drive root shortcuts (`C:\`, `D:\`, `d:\Dev\repos`), glob/regex query input, category filter pills (Code, Docs, Images, Media, Archives, Apps), interactive data table with sorting and pagination, file preview drawer (text, hex, image), direct CSV/JSON exports, and `localStorage` search history.
- **Standalone C++ Server Mode**: Added `--standalone` / `standalone` / `console` interactive mode to `FastSearchServiceNew.exe` with `SetConsoleCtrlHandler` for Ctrl+C interception, allowing execution directly in terminal without administrative Windows SCM setup.
- **Flexible CLI Argument Parsing**: Updated C++ `wmain` in `fastsearch_service.cpp` to parse both standard commands (`install`, `uninstall`, `start`, `stop`) and flag-style commands (`--install`, `--uninstall`, `--start`, `--stop`).
- **Direct REST API Endpoints**: Added dedicated REST API routes in `api_bridge.py`: `POST /api/search`, `GET /api/service/status`, `POST /api/service/start`, `POST /api/service/stop`, `POST /api/service/restart`, and `GET /api/file`.
- **500 Error Crash Prevention**: Wrapped REST API bridge and `call_tool` exception handlers to return structured `{ "success": false, "service_down": true, "error": "..." }` responses instead of unhandled HTTP 500 server crashes.

### Fixed
- **Dashboard UI Mock Gaslights**: Refactored `dashboard.tsx` to remove all static hardcoded mock numbers (records, latency, fake USN consistency claims). It now queries live service status from `/api/service/status` in real time.
- **Unit Test Suite Modernization**: Updated Pytest unit tests in `tests/unit/` (`test_comprehensive.py`, `test_fastsearch.py`, `test_implementation.py`, `test_exceptions.py`, `test_ntfs_tools.py`, `test_service_tools.py`), reaching 100% test pass rate (17/17 passed).

## [0.5.0] — 2026-06-14

### Added
- **FastMCP 3.2 Upgrade**: Sampling (`ctx.sampling()`), CodeMode (`--agentic`), `@mcp.prompt()`, and `@mcp.skill()` support.
- **MFT_RECORD_HEADER USA fixup**: Apply Update Sequence Array fixup to each MFT record before parsing attributes.

### Fixed
- **C++ MFT_RECORD_HEADER struct misalignment**: Fixed `WORD Flags` offset to prevent skipping records.
- **Session management**: Fixed session popping bugs in `mcp_server.py`.
- **Windows named pipe handle leak**: Fixed kernel handle leak in `pipe_client.py`.

## [0.4.0] — 2025-11-15

### Added
- **Fast service availability checks**: Optimized service health check to <1ms per check.
- **Improved error messages**: Step-by-step recovery instructions when service is offline.
