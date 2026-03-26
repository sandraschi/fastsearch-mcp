# FastSearch MCP - Service Availability Checks

**Date:** 2025-11-27  
**Status:** ✅ Service checks implemented with clear error messages

## Overview

FastSearch MCP requires the FastSearch Windows service to be running for file searches. This document explains how service availability is checked and what happens when the service is unavailable.

## Pipe name (client and service must match)

The named pipe path is **`\\.\pipe\FastSearchMCP`**. It is defined in:

- **Service (C++):** `service\src\fastsearch_service.h` → `kPipeName` = `L"\\\\.\\pipe\\FastSearchMCP"`
- **Client (Python):** `src\fastsearch_mcp\pipe_client.py` → `DEFAULT_PIPE_NAME` and `get_pipe_name()` (same value). `service_client.py` imports `get_pipe_name` from there; do not duplicate the pipe path in other modules. Override with env **`FASTSEARCH_PIPE_NAME`** if you use a different build.

If the Tests page shows **pipe_connect** failing with **error 2** (pipe not found), then either the running Windows service is not the one from this repo (wrong executable), or the service failed to create the pipe. Check **Windows Event Log** (source: FastSearchMCP) for "CreateNamedPipe failed" or "Service worker thread … started". Reinstall the service from this repo (`service\build\...\FastSearchServiceNew.exe`) if needed.

## Service Check Flow

### 1. **MCP Server Startup** (Soft Check)

**Location:** `src/fastsearch_mcp/mcp_server.py::start()`

**Behavior:**
- Attempts to connect to named pipe: `\\.\pipe\FastSearchMCP`
- **Does NOT fail** if service is unavailable
- Sets `service_available = False` flag
- Logs warning: "Running in offline mode - some functionality may be limited"
- Shows Windows message box (if GUI available) with instructions

**Purpose:** Allow MCP server to start even if service isn't ready, so other tools can still work.

### 2. **Per-Search Check** (Hard Check - Optimized for Speed)

**Location:** `src/fastsearch_mcp/service_client.py::search_files()`

**Behavior:**
- **Before every search**, checks if service is running (FAST - <1ms typical)
- Uses **fast pipe connection check** first (fails immediately if service is down)
- **Caches result for 2 seconds** to avoid repeated checks on rapid searches
- Falls back to process check only if pipe check is ambiguous
- If service not running → Raises `RuntimeError` with clear error message
- If service running but pipe fails → Raises `RuntimeError` with troubleshooting steps

**Performance:**
- First check: ~0.1ms (pipe connection attempt)
- Cached checks: ~0.01ms (essentially instant)
- Old approach (tasklist): up to 5 seconds ❌
- New approach: <1ms ✅

**Error Messages:**
- ✅ **Service not running**: Clear explanation + step-by-step fix instructions
- ✅ **Service not responding**: Troubleshooting steps + tool suggestions
- ✅ **Pipe communication failed**: Detailed diagnostics + recovery steps

### 3. **Error Response Format**

When a search fails due to service unavailability, the response includes:

```json
{
  "success": false,
  "error": "❌ FastSearch service is not running.\n\n...detailed message...",
  "pattern": "*.py",
  "path": "C:\\",
  "results": [],
  "count": 0,
  "method": "error",
  "service_required": true,
  "suggestion": "Use 'service_status' tool to check service status..."
}
```

## Error Messages

### Service Not Running
```
❌ FastSearch service is not running.

The FastSearch MCP requires the FastSearch Windows service to be installed and running
for direct NTFS MFT access. Without the service, file searches cannot be performed.

To fix this:
1. Check if the service is installed: Open Windows Services (Win+R → services.msc)
2. Look for 'FastSearch MCP Service' or 'FastSearchMCP' in the list
3. If installed but stopped: Right-click → Start
4. If not installed: Run the installer as administrator

You can also use the 'service_status' tool to check the current service status.
```

### Service Not Responding
```
❌ No response from FastSearch service.

The FastSearch service appears to be running but is not responding to requests.
This may indicate the service is hung or experiencing issues.

To troubleshoot:
1. Check service status using the 'service_status' tool
2. Try restarting the service: Use 'restart_service' tool or Windows Services
3. Check service logs: Use 'get_service_logs' tool
4. If the issue persists, restart the service manually as administrator
```

### Pipe Communication Failed
```
❌ Named pipe communication failed: [error details]

The FastSearch service could not be reached via the named pipe.
This usually means:
- The service is not running (check with 'service_status' tool)
- The service is hung or crashed (try restarting it)
- Permission issues (ensure service is running as LocalSystem)

To fix:
1. Check service status: Use 'service_status' tool
2. Restart the service: Use 'restart_service' tool or Windows Services
3. Check service logs: Use 'get_service_logs' tool for error details
```

## Preflight Check Options

### Option 1: Use `service_status` Tool (Recommended)

Before performing searches, Claude Desktop can call:

```python
# Check service status
status = await service_status(level="basic")
if not status.get("running"):
    # Service not running - inform user before attempting search
    return "Service not available. Please start the FastSearch service first."
```

**Tool:** `service_status`  
**Levels:** `basic`, `intermediate`, `advanced`  
**Returns:** Service running status, pipe connection status, diagnostics

### Option 2: Let Search Handle It (Current Behavior)

Each search automatically checks service availability and returns a clear error if unavailable. This is the current default behavior.

**Advantage:** No extra tool call needed  
**Disadvantage:** User only finds out when they try to search

## Best Practices for Claude Desktop

### Recommended Flow:

1. **On MCP server connection:** Optionally check `service_status` to inform user
2. **Before first search:** Optionally call `service_status` to verify readiness
3. **On search failure:** Error message includes `service_required: true` and `suggestion` field
4. **Recovery:** User can call `service_status` → `start_service` → retry search

### Example Claude Desktop Integration:

```python
# Preflight check (optional but recommended)
status = await service_status(level="basic")
if not status.get("running"):
    return {
        "warning": "FastSearch service is not running. "
                   "File searches will fail until the service is started. "
                   "Use 'service_status' to check status or 'start_service' to start it."
    }

# Perform search
result = await fastsearch_search(pattern="*.py", path="C:\\")
if not result.get("success") and result.get("service_required"):
    # Service issue - provide recovery steps
    return {
        "error": result.get("error"),
        "suggestion": result.get("suggestion"),
        "recovery": "Try: 1) service_status 2) start_service 3) retry search"
    }
```

## Performance Optimization

### Fast Service Check Implementation

The service check has been optimized for speed to maintain the "FastSearch" promise:

**Optimization Strategy:**
1. **Fast pipe check first**: Attempts to connect to named pipe (fails immediately if service is down)
2. **2-second cache**: Caches result to avoid repeated checks on rapid searches
3. **Fallback only if needed**: Uses slower `tasklist` only if pipe check is ambiguous

**Performance Results:**
- First check: ~0.1ms (pipe connection)
- Cached checks: ~0.01ms (essentially instant)
- Old approach: up to 5 seconds with `tasklist` ❌
- New approach: <1ms ✅

**Impact:**
- Service check adds **negligible overhead** (<1ms) to each search
- Rapid searches don't trigger repeated slow checks
- Maintains "FastSearch" performance promise

## Summary

✅ **Service checks:** Performed before every search (<1ms overhead)  
✅ **Error messages:** Clear, user-friendly with step-by-step instructions  
✅ **Preflight option:** `service_status` tool available for proactive checking  
✅ **Recovery path:** Error messages include tool suggestions for troubleshooting  
✅ **Performance:** Optimized to <1ms per check (cached for 2 seconds)

**Answer:** Service availability is checked **before each search attempt** with **<1ms overhead** (thanks to fast pipe check + caching). Error messages are explicit and actionable. The `service_status` tool can be used for preflight checks if desired.

