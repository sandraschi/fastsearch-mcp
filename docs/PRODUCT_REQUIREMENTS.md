# FastSearch MCP - Product Requirements Document (PRD)

**Project:** FastSearch MCP Server  
**Version:** 2.4  
**Date:** August 2026  
**Status:** ✅ Production Ready - Dedicated SOTA Search Page, direct REST API bridge, interactive standalone engine mode, zero-mock live health metrics.

---

## 📋 Executive Summary

FastSearch MCP gives Claude Desktop and Web applications instant, large-scale file search on Windows by reading the NTFS Master File Table (MFT) on demand. A privileged C++ Windows service performs the MFT scan while a user-mode Python MCP bridge exposes tools to Claude, alongside a direct FastAPI REST bridge and SOTA React Search UI (`/search`). We explicitly reject traditional indexing, caching, or background scanning so startup stays instant and results remain live.

---

## 🎯 Product Vision

**"Deliver WizFile-class search speed inside Claude Desktop without sacrificing startup time, accuracy, or system stability."**

### Core Value Proposition

- ⚡ **Instant results**: Live NTFS MFT access, no pre-computed index.
- 🧠 **Claude-native**: Structured FastMCP tools with rich schemas and documentation.
- 🔒 **Secure privilege separation**: Elevated C++ service + user-mode MCP bridge.
- 🪶 **Lightweight**: Memory footprint below 50 MB with no persistent stores.
- 🎯 **Precise**: Results always reflect the current filesystem; deleted files never linger.
- ⚡ **Fast service checks**: <1ms overhead per search (optimized from 5 seconds).

---

## 🚨 Non-Negotiable Principles

1. **Direct MFT Access Only**
   - Every search must read the NTFS MFT in real time.
   - No background indexing, recursive directory walking, or caching of file metadata.

2. **Instant Startup**
   - Both service and bridge must start in under one second.
   - Service may not perform work until the first request arrives.

3. **Predictable Resource Usage**
   - Peak memory under 50 MB even on multi-million file volumes.
   - No allocations proportional to total file count.

4. **Early Termination**
   - Respect `max_results`; stop scanning as soon as the cap is reached.
   - Honour path and filter constraints before emitting results to the bridge.

5. **No Fallbacks**
   - Direct MFT access is required - no treewalking fallbacks allowed.
   - When service is unavailable, clear error messages with recovery steps must be provided.
   - Architecture requires service to be running for searches to function.

---

## 🏗 Functional Requirements

### 1. `file_search` (fastsearch_search)
- Input: pattern, optional drive/path filters, `max_results`.
- Processing: stream the NTFS MFT, apply filters, stop at `max_results`.
- Output: ordered list of matches with path, size, timestamps, and method indicator.
- Latency target: < 100 ms on SSD-backed systems for typical patterns.
- **Status:** ✅ Fully operational - All patterns, drives, and directories tested and working.

### 2. `disk_analyzer`
- Identify the largest files/directories on a drive.
- Reuses the MFT stream with size sorting limited to the top N entries.

### 3. `duplicate_finder` (optional/experimental)
- Uses file size + metadata heuristics; may require additional per-file hashing after initial MFT pass (performed lazily, never cached globally).

### 4. Service Management Tools
- `service_status`, `start_service`, `stop_service`, `get_service_logs`, etc. provide operational control and diagnostics.
- **Status:** ✅ All service management tools operational.

---

## 🤝 Integration Requirements

### Claude Desktop MCP
- Full FastMCP 2.13 compliance: tool discovery, JSON schema validation, streaming responses.
- Rich documentation metadata so Claude knows how and when to call each tool.
- Clear error signalling for privilege issues or service downtime.
- **Status:** ✅ FastMCP 2.13 compliant, all 18 tools functional.

### Diagnostics & Tooling
- PowerShell scripts (`install-service.ps1`, `debug-service-startup.ps1`, `scripts/read-service-logs.ps1`) must remain up to date.
- Logs must surface privilege failures, pipe errors, and service availability issues.
- Service status checks optimized to <1ms overhead per search.
- **Live testing:** Webapp **Tests** page (`/tests`) and API `POST /api/tests/run` run integration tests (service process, pipe connect, get_service_info, real search via pipe). Pytest `tests/test_live_pipe.py` runs the same flow (marked `@pytest.mark.service`, Windows-only).
- **Path normalization:** Search path input (e.g. `C:`) is normalized to a format the C++ service accepts (e.g. `C:\\`) to avoid empty results from format mismatch.
- **Status:** ✅ All diagnostic tools operational, fast service checks implemented, live tests and Tests page available.

---

## 🧩 Technical Requirements

| Domain | Requirement |
|--------|-------------|
| **Service Language** | C++17 (Visual Studio toolchain). |
| **Bridge Language** | Python 3.10+ with `fastmcp` integration. |
| **Privileges** | Service runs as `LocalSystem`; bridge runs as standard user. |
| **IPC** | Named pipe `\\.\pipe\FastSearchMCP` with JSON messages. |
| **Filesystem Support** | Windows NTFS volumes only. Direct MFT access requires NTFS filesystem. |

### Error Handling
- Service failures must emit Event Log entries and return structured errors to the bridge.
- Bridge responses must include remediation advice (e.g. "Run install-service.ps1 start as Administrator").
- **Status:** ✅ Clear, actionable error messages with step-by-step recovery instructions implemented.

### Security
- No sensitive data persisted. Logs include only necessary metadata and error details.
- Pipe ACL restricted to the launching user session.
- No network access.

---

## 📊 Success Metrics

| KPI | Target | Measurement | Status |
|-----|--------|-------------|--------|
| Search latency | < 100 ms (95th percentile, SSD, 1M files) | `tests/test_fastsearch.py` benchmark. | ✅ Achieved |
| Memory usage | < 50 MB at peak | Windows Performance Monitor / internal counters. | ✅ Achieved |
| Startup time | < 1 s for both bridge and service | Stopwatch instrumentation. | ✅ Achieved |
| Accuracy | 100% live filesystem fidelity | Regression tests + manual validation. | ✅ Achieved |
| Service check overhead | <1ms per search | Optimized pipe check with caching. | ✅ Achieved (<1ms) |
| Test coverage | 18/18 tests passing | Comprehensive test suite validates all scenarios. | ✅ 18/18 passing |

---

## 🧪 Testing Strategy

- **Unit Tests:** pattern parsing, parameter validation, error handling.
- **Integration Tests:** named pipe contract, service lifecycle scripts, privilege checks.
- **Live pipe tests:** `fastsearch_mcp.live_tests.run_live_tests()` and `tests/test_live_pipe.py` run real pipe connection and real search against the C++ service (Windows, service must be running). Webapp **Tests** page invokes the same flow via `POST /api/tests/run`.
- **Performance Harness:** repeatable MFT scanning benchmarks (requires elevated PowerShell session).
- **Manual QA:** Event log review, service start/stop cycles, failure injection.
- **Status:** ✅ Comprehensive test suite (18/18 tests passing) plus live pipe integration tests and webapp Tests page.

---

## 🛡 Risk Management

| Risk | Mitigation | Status |
|------|------------|--------|
| Service unavailability | Fast service checks (<1ms), clear error messages with recovery steps, `service_status` tool for diagnostics. | ✅ Mitigated |
| Loss of elevation | Detect quickly, return actionable message, guide user to reinstall/start service. | ✅ Mitigated |
| Architecture drift toward indexing | Maintain documentation warnings, enforce during code review, add automated linting for banned patterns if necessary. Removed all fallback code. | ✅ Mitigated |
| Cross-user pipe access | Maintain restricted ACLs and verify during install script execution. | ✅ Mitigated |
| Slow service checks | Optimized pipe connection check with 2-second caching to maintain <1ms overhead. | ✅ Mitigated |

---

## 🔜 Roadmap Highlights

1. ✅ **Service operational** - FastSearch Windows service running and responding (November 2025).
2. ✅ **Search functionality** - All search tools working with direct NTFS MFT access.
3. ✅ **Performance optimized** - Service checks optimized from 5 seconds to <1ms.
4. ✅ **Architecture cleanup** - Removed all fallback code (direct MFT access only).
5. ✅ **Error handling** - Clear, actionable error messages with recovery steps.
6. ✅ **Live tests and Tests page** - Integration tests (pipe + real search) in pytest and webapp at `/tests` (March 2025).
7. **Enhance diagnostics** with optional pipe-level tracing (on-demand, not persistent).
8. **Explore additional tools** (e.g. permission reporting) while respecting zero-indexing rules.

---

## 📝 Recent Achievements (August 2026)

- ✅ **Dedicated SOTA Search Page (`/search`)** - Interactive search UI with live service status badge, drive shortcuts (`C:\`, `D:\`), category filters, sorting/pagination, file preview drawer (text, hex, image), export (CSV/JSON), and `localStorage` history.
- ✅ **Standalone C++ Engine Mode** - Interactive `--standalone` / `standalone` mode for `FastSearchServiceNew.exe` with Ctrl+C handler for non-SCM execution.
- ✅ **Direct REST API Endpoints** - FastAPI routes in `api_bridge.py`: `/api/search`, `/api/service/status`, `/api/service/start`, `/api/service/stop`, `/api/service/restart`, `/api/file`.
- ✅ **Zero-Mock Dashboard** - Refactored `dashboard.tsx` to remove all static mock gaslights, querying live REST service status in real time.
- ✅ **500 Error Prevention** - Structured error responses (`"service_down": true`) on pipe disconnections, eliminating server crashes.
- ✅ **100% Test Pass Rate** - 17/17 unit tests passing cleanly in `tests/unit/`.

## 📝 Recent Achievements (March 2025)

- ✅ **Live integration tests** - Real pipe + real search tests; pytest `test_live_pipe.py` and webapp Tests page at `/tests`
- ✅ **Path normalization** - Search paths (e.g. `C:`) normalized to `C:\\` for C++ service compatibility
- ✅ **Pipe error reporting** - Pipe connection failures no longer reported as success with 0 results; clear errors in UI

## 📝 Recent Achievements (November 2025)

- ✅ **Search functionality fully operational** - All search tools tested and working
- ✅ **Service running** - FastSearch Windows service operational and responding
- ✅ **Performance optimized** - Service checks reduced from 5 seconds to <1ms
- ✅ **Architecture preserved** - All fallback code removed, direct MFT access only
- ✅ **Error messages improved** - Clear, actionable guidance for users
- ✅ **Test coverage complete** - 18/18 comprehensive tests passing

See `docs/RECENT_IMPROVEMENTS.md` for detailed information on recent improvements.

---

Keeping the documentation aligned with the C++ service + Python bridge architecture is essential. Any proposal that introduces indexing, caching, or long-running scans must be rejected before implementation.
