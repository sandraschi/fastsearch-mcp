
## [Unreleased] — 2026-06-14

### Added
- Tauri 2.0 native wrapper with `bundle.resources` + `std::process::Command`
- PyInstaller frozen backend embedded in NSIS installer
- CUA-NSIS smoke test (`scripts/cua-smoke.py`, `scripts/cua-nsis-config.json`)
- `just cua-nsis-test` recipe
- Tauri CORS: `tauri://localhost` origins for WebView API access
- `GET /api/v1/diagnostics` endpoint for CUA verification
# Changelog

All notable changes to FastSearch MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **MFT_RECORD_HEADER USA fixup** - Apply Update Sequence Array fixup to each MFT record before parsing attributes. Without this, the last 2 bytes of each 512-byte sector contained fixup values instead of real data, corrupting attribute traversal when attributes crossed sector boundaries.

### Fixed
- **C++ MFT_RECORD_HEADER struct misalignment** - The `WORD Flags` field was missing between `AttributeOffset` (0x14) and `BaseRecordReference` (0x18), placing it at offset 0x26 instead of 0x16. This caused the record-in-use check (`header->Flags & 0x0001`) to read the high word of the MFT record number instead of the actual flags, silently skipping ~50% of records. (mft_search.cpp)
- **Session management completely broken** - `mcp_server.py` popped `session_id` from params twice, discarding the first session and creating a brand-new UUID session on every request. Session state, history, and search history were all lost. (mcp_server.py:233-243)
- **Windows named pipe handle leak** - On pipe I/O errors, `self.connected` was set to `False` but `self.handle` was never closed via `CloseHandle`, leaking the kernel handle. (pipe_client.py:196-203)
- **Blocking CreateFile in async connect** - `win32file.CreateFile` for named pipes can block for seconds waiting for an available instance, freezing the asyncio event loop. Wrapped in `run_in_executor` with `asyncio.wait_for`. (pipe_client.py:75-88)
- **Service arguments passed as joined string** - `win32serviceutil.StartService` received `" ".join(args)` which caused pywin32 to iterate over individual characters, turning `["--verbose", "--port=8080"]` into 20 single-character arguments. (service_manager.py:324)
- **Blocking subprocess.run in async functions** - `subprocess.run` calls in `get_service_status`, `start_service`, and `stop_service` blocked the event loop for up to 30 seconds. Wrapped in `asyncio.to_thread`. (service_client.py)
- **Date filters silently dropped on parse failure** - Invalid date strings (typos, wrong formats) returned `None` from the parser, which was silently ignored. Users got unfiltered results instead of an error. All six date parameters now validated at tool entry with immediate error return. (advanced_search.py, file_search.py)
- **Multi-drive search double truncation** - `file_name_search.py` unnecessarily truncated combined results to `max_results` after per-drive limits were already applied, discarding results from later drives. (file_name_search.py:269-270)
- **New files reported as "updated"** - `integrity_checker.py` called `add_file` (which inserted into `self.records`) before checking `file_path_str in self.records`, making the check always True and the "added" code path dead when `update_existing=True`. (integrity_checker.py:381-388)
- **CSV/TSV include_metadata silently discarded** - Metadata lines appended to `content_lines` were never joined into the final CSV/TSV output (only used for markdown/Pandoc). Prepend metadata to CSV/TSV string output. (search_result_export.py:418-434)
- **PYTHONIOENCODING=ascii:replace corrupts stderr** - Set `PYTHONIOENCODING=ascii:replace` in `__main__.py`, silently replacing all non-ASCII characters with `?` in log/error output. Changed to `utf-8:replace`. (__main__.py:26)
- **_sanitize_for_json corrupts bytes** - Decoded arbitrary bytes as ASCII with replacement, silently corrupting binary data. Now uses `base64.b64encode`. (base.py:90-91)
- **UTF-8 truncation reclassifies text as binary** - File truncation at `MAX_TEXT_BYTES` could land mid-multi-byte character, causing `UnicodeDecodeError`. The file was reclassified as binary (base64 blob). Now trims to a clean character boundary. (api_bridge.py:143-149)
- **mcp.disable() failures hidden silently** - Bare `except Exception: pass` swallowed all failures from `mcp.disable()`, leaving unwanted tools registered. Now logs a warning and catches only `LookupError`. (tools/__init__.py:154-158)

### Changed
- **Version bump** - 0.4.0 → 0.5.0
- **FastMCP upgrade 3.1 → 3.2** - Dependency updated to `fastmcp>=3.2.0,<4`
  - **Sampling**: Tools now use `ctx: Context = None` pattern for client-side LLM sampling via `ctx.sampling()`
  - **CodeMode**: New `--agentic` CLI flag (and `MCP_AGENTIC=true` env) enables agentic discovery via `CodeMode().attach(mcp)`, collapsing tools into search + execute meta-tools
  - **Prompts**: 3 `@mcp.prompt()` templates registered: file search guide, disk analysis guide, service troubleshooting
  - **Skills**: 3 `@mcp.skill()` definitions: find recently modified files, cleanup disk space, forensic file audit
  - **Transport**: Updated to support FastMCP 3.2 async APIs (`run_stdio_async`, `run_http_async`)
- **mcpb.json** - Updated fastmcp constraint to `>=3.2.0,<4`, version bumped to 1.1.0
- **ntfs.py** - Changed `bytes(n)` to `bytearray(n)` for mutable DeviceIoControl output buffer (was passing immutable bytes object).
- **Documentation updated** - Stale FastMCP 2.13 references replaced with 3.2 throughout

## [0.4.0] - 2025-11-15

### Added
- **Fast service availability checks** - Optimized from 5 seconds to <1ms per check
  - Fast pipe connection check (fails immediately if service is down)
  - 2-second caching to avoid repeated checks on rapid searches
  - Fallback to process check only if pipe check is ambiguous
- **Improved error messages** - Clear, user-friendly error messages with step-by-step recovery instructions
  - Service-required flags in search responses
  - Tool suggestions for troubleshooting (`service_status`, `start_service`, etc.)
- **Comprehensive test coverage** - 18/18 tests passing
  - Tests for different file patterns (*.py, *.cpp, *.txt, etc.)
  - Tests for different drives (C:\, D:\, etc.)
  - Tests for different start directories
  - Tests for search all drives functionality

### Changed
- **Service checks performance** - Reduced from 5 seconds to <1ms overhead per search
- **Error handling** - More explicit and actionable error messages
- **Search response format** - Added `service_required` flag and `suggestion` field

### Removed
- **Fallback code** - Removed all treewalking fallbacks that violated architecture
  - Removed `_fallback_search()` dead code from `service_client.py`
  - Removed `basic_file_search()` treewalker from `mcp_server.py`
  - Removed `fastsearch.search_basic` tool registration
- **Python fallback references** - Updated all documentation to reflect direct MFT access only

### Fixed
- **Search functionality** - All search tools now fully operational
  - File searches working across different patterns, drives, and directories
  - Service integration complete - FastSearch Windows service running and responding
  - Direct NTFS MFT access verified and working

### Documentation
- Created `CHANGELOG.md` - Project changelog following Keep a Changelog format
- Created `docs/RECENT_IMPROVEMENTS.md` - Comprehensive documentation of recent improvements
- Created `docs/SERVICE_AVAILABILITY_CHECKS.md` - Detailed explanation of service check flow
- Updated `README.md` - Reflects current operational status
- Updated `docs/STATUS_REPORT.md` - Updated with recent improvements and current status
- Updated `docs/TECHNICAL_ARCHITECTURE.md` - Removed fallback references, updated status
- Updated `docs/PRODUCT_REQUIREMENTS.md` - Updated to version 2.2, reflects production-ready status, removed fallback references

## [0.4.0] - 2025-11-15

### Added
- Direct NTFS MFT access implementation
- FastMCP 2.13 compliant MCP server
- Comprehensive tool suite (18 tools)
- Service management tools
- Advanced search with MFT attribute filtering

### Changed
- Architecture to direct MFT access only (no indexing, no caching)

## [0.3.0] - Previous Release

### Added
- Initial MCP bridge implementation
- Basic file search functionality
- Service infrastructure

---

[Unreleased]: https://github.com/sandraschi/fastsearch-mcp/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/sandraschi/fastsearch-mcp/releases/tag/v0.5.0
[0.4.0]: https://github.com/sandraschi/fastsearch-mcp/compare/v0.3.0...v0.4.0


