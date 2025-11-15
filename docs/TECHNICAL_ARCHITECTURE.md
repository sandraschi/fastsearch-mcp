# FastSearch MCP - Technical Architecture

**Project:** FastSearch MCP Server  
**Date:** November 2025  
**Architecture:** Direct NTFS Master File Table access with C++ service + Python MCP bridge

---

## 1. Architectural Philosophy

FastSearch MCP deliberately mirrors the WizFile approach: every search reads the NTFS Master File Table (MFT) directly. We do **not** build indexes, walk directory trees in advance, or cache file metadata.

| Principle | Expectation |
|-----------|-------------|
| **Zero Indexing** | No startup scans, no background workers, no cached file lists. |
| **Live Data** | Each query opens the MFT and streams results until `max_results` is reached. |
| **Instant Startup** | Process startup must remain sub-second. |
| **Minimal Memory** | Peak usage < 50 MB; no persistent allocations proportional to file counts. |
| **Deterministic Stop** | Stop scanning immediately once the caller’s `max_results` limit is satisfied. |

Any optimisation that contradicts these constraints (e.g. LRU caches, pre-built databases, recursive directory walks) is considered an architectural regression and must be rejected.

---

## 2. High-Level Components

```
Claude Desktop ──JSON-RPC── Python MCP Bridge ──Named Pipe── C++ Service ── NTFS MFT
```

### 2.1 Python MCP Bridge (`src/fastsearch_mcp/`)
- Runs with standard user privileges.
- Implements the FastMCP 2.13 schema for all tools (file search, disk analysis, service management, etc.).
- Routes file-search requests to the service via the named pipe `\\.\pipe\FastSearchMCP`.
- Provides **explicitly degraded** Python fallbacks when the service is offline (recursive glob + filters). Fallbacks must surface warnings so users restore direct MFT access.

### 2.2 C++ Windows Service (`service/`)
- Runs as `LocalSystem` after a one-time elevated install.
- Owns all direct NTFS interactions. Opens volume handles (`\\.\C:` etc.), reads the MFT via Windows filesystem APIs, and streams matching entries back to the bridge.
- Exposes a duplex named pipe accepting JSON requests and streaming JSON responses.
- Emits structured diagnostics to the Windows Event Log (source: `FastSearchMCP`). Logging is mandatory for each init step to aid Event ID 7034 crash triage.

### 2.3 Communication Contract
- **Protocol:** newline-delimited JSON with UTF-8 payloads.
- **Request envelope:** `{ "id": <uuid>, "tool": "file_search", "params": {...} }`
- **Response envelope:** `{ "id": <uuid>, "status": "ok" | "error", "data": {...} }`
- The bridge enforces `max_results` and aborts the pipe read once enough entries have been returned.

---

## 3. Direct NTFS MFT Access

### 3.1 Volume Access

```cpp
// Simplified: see service/src/fastsearch_service.cpp
HANDLE volume = CreateFileW(
    L"\\\\.\\C:",
    GENERIC_READ,
    FILE_SHARE_READ | FILE_SHARE_WRITE,
    nullptr,
    OPEN_EXISTING,
    FILE_FLAG_BACKUP_SEMANTICS,
    nullptr);
```

- The service elevates required privileges (`SeBackupPrivilege`) during startup; failures are logged and surfaced to the bridge.
- Volumes are opened on demand per request; we do **not** keep long-lived handles when idle.

### 3.2 Enumerating the MFT

**IMPLEMENTED:** Direct MFT reading via LCN (Logical Cluster Number) - November 2025

```cpp
// Get MFT start location from volume data
NTFS_VOLUME_DATA_BUFFER volumeData;
GetNtfsVolumeData(hVolume, volumeData);
ULONGLONG mftStartLcn = volumeData.MftStartLcn.QuadPart;
DWORD recordSize = volumeData.BytesPerFileRecordSegment;
DWORD bytesPerCluster = volumeData.BytesPerCluster;

// Read MFT records directly from volume using LCN offsets
ULONGLONG recordNumber = 5;  // Start from first user file
while (results.size() < maxResults) {
    // Calculate absolute byte offset from MFT start LCN
    ULONGLONG recordOffsetInBytes = recordNumber * recordSize;
    ULONGLONG clusterOffset = recordOffsetInBytes / bytesPerCluster;
    ULONGLONG targetLcn = mftStartLcn + clusterOffset;
    
    // Seek to record location and read directly
    LARGE_INTEGER seekPos;
    seekPos.QuadPart = targetLcn * bytesPerCluster + (recordOffsetInBytes % bytesPerCluster);
    SetFilePointerEx(hVolume, seekPos, nullptr, FILE_BEGIN);
    ReadFile(hVolume, recordBuffer.data(), recordSize, &bytesRead, nullptr);
    
    // Parse FILE_NAME attribute and match pattern
    if (ParseFileNameAttribute(recordBuffer, fileName, ...)) {
        if (MatchPattern(fileName, pattern)) {
            send_result(fileName);
        }
    }
    recordNumber++;
}
```

**Key Implementation Details:**
- **Direct LCN-based reading**: Uses `FSCTL_GET_NTFS_VOLUME_DATA` to get MFT start LCN, then reads records directly from volume handle
- **No file system API calls**: Bypasses `FindFirstFile`, `FindNextFile`, and all directory traversal
- **Pattern matching**: Simple glob-to-regex conversion with case-insensitive matching
- **Early termination**: Stops immediately when `max_results` is reached
- **Streaming**: Records are parsed and emitted one-by-one, never stored in bulk
- **Real-time accuracy**: Every search reads live MFT data - no stale caches

**Performance Validation:**
- Tested: 100 results from 5,008 MFT records scanned in <1 second
- Memory: <50MB peak usage (no caching)
- Startup: <1 second (no indexing)

### 3.3 Error Handling

- All service operations return `Status` structs with Windows error codes.
- Failures are logged via `SvcLogMessage(level, message, error_code)` and relayed to the bridge so Claude can message the user.
- Bridge methods wrap errors with `anyhow::Context` (Python side uses `fastmcp` error helpers) to provide actionable responses.

---

## 4. Request Lifecycle

1. Claude invokes `file_search` with JSON arguments.
2. The MCP bridge validates and normalises parameters (pattern, drive, max_results).
3. The bridge writes a JSON request to the named pipe and awaits streamed results.
4. The service opens the requested NTFS volume, scans the MFT, and emits matching entries one-by-one.
5. Once `max_results` is reached—or the MFT is exhausted—the service sends a completion frame.
6. The bridge forwards results to Claude and records telemetry counters (in-memory only).

If the service is unavailable, step 3 fails; the bridge logs a warning and executes the Python fallback with a prominent degradation notice.

---

## 5. Performance Targets & Validation

| Metric | Target | Notes |
|--------|--------|-------|
| Service start | < 1 s | No background work permitted. |
| Search latency | < 100 ms for typical patterns on SSDs | Achieved via direct MFT streaming and early termination. |
| Memory usage | < 50 MB | Verified with Windows Performance Monitor; no caches allowed. |
| Result freshness | Real-time | Direct MFT read guarantees live state. |

Performance testing scripts live under `tests/` and `scripts/`. Run `python test_fastsearch.py` with elevated privileges to exercise the fast path.

---

## 6. Diagnostics & Logging

- **Event Log Source:** `FastSearchMCP`
- **Key startup checkpoints:**
  1. Service control registration
  2. Privilege enablement
  3. Named pipe creation
  4. Worker thread launch
  5. Volume probe

`debug-service-startup.ps1` collects these logs and verifies registry entries, service configuration, and pipe connectivity. `read-service-logs.ps1` filters entries by severity for quick triage.

---

## 7. Fallback Behaviour

- Python fallback (`service_client._fallback_search`) uses `Path.rglob` + `fnmatch`.
- Fallbacks must never be silently upgraded to long-running crawlers; they exist solely to keep the tool responsive when elevation is unavailable.
- The bridge labels fallback results with `method: "fallback_python"` so Claude can signal reduced fidelity.

---

## 8. Security & Permissions

- Service binaries run as `LocalSystem`; installation requires Administrator once.
- Named pipe ACLs restrict access to the current interactive user session to prevent cross-user leakage.
- No file contents are read—only metadata from the MFT.
- No telemetry, network egress, or persistent storage is produced.

---

## 9. Current Status & Open Work

- Service installs reliably via `install-service.ps1`.
- Some environments still hit Event ID 7034 during startup; see `docs/SERVICE_DEVELOPMENT_STATUS.md` for the debugging checklist.
- Named pipe contract is stable; any schema changes must be mirrored between `fastsearch_service` and `service_client.py`.

---

Maintaining this architecture is non-negotiable. Changes that drift toward traditional indexing must be blocked during review and escalated immediately.
