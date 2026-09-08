# Changelog

All notable changes to FastSearch MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] — 2026-09-08

### Added
- **Python REST bridge is now a proper NSSM Windows service** (`fastsearch-mcp`, distinct from the existing native `FastSearchMCP` NTFS service). Previously just a bare `uv run uvicorn ...` process started by hand — nothing restarted it on crash or reboot, and the fleet launcher's port-conflict check treated it as an ordinary squatter rather than a persistent backend. `fleet-start.config.ps1` now declares `Kind='nssm'` with an explicit `NssmService` override.
- **`$DATA` attribute parsing for authoritative file size** (`service/src/mft_search.cpp`): the scanner previously read size only from `$FILE_NAME`'s cached `RealSize`/`AllocatedSize` fields, which NTFS doesn't reliably keep current on every write — most files reported size 0 or a stale value. `ParseDataAttribute()` reads size directly from the unnamed `$DATA` attribute (resident `ValueLength`, or the fixed-offset `RealSize`/`AllocatedSize` header fields for non-resident — no data-run decoding needed just for size).
- **Real parent-chain path resolution** (`ResolveFullPath()`): files previously reported only a bare filename with an unresolved `parent_dir` MFT reference — nothing showed a real folder, so results couldn't be located in Explorer. Walks the `$FILE_NAME` `ParentDirectory` chain up to the volume root, per-thread cached (each scan worker already owns its own volume handle, so no locking needed). Validated with three checks before trusting a resolved ancestor: valid "FILE" signature, sequence number matches what the reference expected (catches a recycled record slot), and the record's own self-reported `RecordNumber` matches what was requested (catches a read landing at the wrong physical offset entirely).

### Fixed
- **Cushion treemap layout was a flat horizontal strip, not a 2D squarified layout** (`web_sota/src/components/CushionTreemap.tsx`): `layoutSquarified` was named and commented as the Bruls/Huizing/van Wijk algorithm but didn't implement it — it placed every child of a node in a single row or column based on one global width-vs-height check, a 1D proportional strip rather than 2D squarification. Replaced with an actual squarified layout: builds one row at a time along the container's current shorter side, greedily adding children only while it doesn't worsen the row's worst aspect ratio, closes the row, recurses into the remainder.
- **Path resolution was fabricating wrong ancestor folder names**: live verification found paths like `C:\PCPKSP\...` and `C:\AggregatorStorage\...` that don't exist anywhere on the volume (confirmed via direct filesystem enumeration). Root cause: `ReadMftRecordFromVolume`'s offset math assumes the volume's `$MFT` is one contiguous extent, which holds for the main sequential scan but not for an ancestor's record number reached by random access on a fragmented `$MFT` — the read can land at the wrong physical offset. Two confirmed failing cases both diagnosed to landing on MFT record #0 (the `$MFT`'s own metadata record), which coincidentally has a valid signature and sequence number, passing the checks already in place. Added a third check (self-reported `RecordNumber` must match what was requested) that catches this. **Known limitation, not fully solved**: this makes the resolver fail safely rather than fabricate a wrong path, but ancestors outside the first `$MFT` extent still can't be resolved and fall back to a flat filename. Full resolution needs the `$MFT`'s own data-run list decoded — scoped as a follow-up, not attempted here given the risk of shipping another unverified native fix.

## [0.6.0] — 2026-08-25

### Added
- **Automated First-Time Onboarding (`just onboard`)**: Created single-UAC onboarding pipeline (`scripts/onboard-first-time-user.ps1`) that prompts for Administrator elevation **ONCE** via UAC to register & start the `FastSearchMCP` background Windows Service under `LocalSystem`, followed by automated unprivileged Win32 Named Pipe IPC diagnostics (`\\.\pipe\FastSearchMCP`).
- **4 Windows Explorer Result Display Modes**: Added layout view switcher toolbar to Search page featuring **Details View** (Sortable Table), **Grid / Medium Icons View** (Responsive Cards), **Tiles View** (Multi-column Cards), and **Compact List View** (High-density Rows).
- **Configurable Results Pagination & Max Limits**: Added switchable page size selector (`25`, `50`, `100`, `250`, `500` per page) and configurable MFT search limit cap (`100`, `250`, `500`, `1,000`, `2,000`, `5,000`, `10,000`).
- **Advanced Sorting & Multi-Dimensional Filtering**: Added multi-attribute sorting (`Sort: Name`, `Sort: Path`, `Sort: Size`, `Sort: Type/Extension`, `Asc/Desc`), category filter pills, size range filter (`Small < 1MB`, `Medium 1-100MB`, `Large > 100MB`), and live search input.
- **Live System Logging for Web App Logs Page (`/logs`)**: Attached custom `RingBufferLogHandler` to Python `logging` framework (`fastsearch_mcp` and `uvicorn`), populating real-time system logs (MFT searches, tool calls, service checks, exceptions) on the `/logs` page with exact timestamps, log levels, file origins, and line numbers.
- **Comprehensive Real-Time Service Diagnostics & Event Logs**: Surfaced SCM/UAC execution traces, exit codes, stderr, and C++ Windows Event Log entries under source `FastSearchMCP` via `GET /api/service/logs` and real-time UI diagnostic drawer.

### Fixed
- **Web UI "Start Service" UAC Elevation**: Added automatic fallback to UAC elevation prompt (`Start-Process powershell -Verb RunAs`) when starting service from unprivileged Web UI.
- **Service Disconnection Diagnostics**: Clarified privilege separation architecture notices across UI, `help.tsx`, and CLI scripts.

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
