# FastSearch MCP - Status note (ops / memops)

**Purpose:** Short ops-friendly status note for the pipe connection problem and where to look.

---

## Status: Pipe connect failure (error 2)

**Symptom:** Tests page or search reports pipe not available; `pipe_connect` shows `connected: false`, often **error 2** (pipe not found).

**Cause:** The named pipe `\\.\pipe\FastSearchMCP` does not exist when the client connects. Either the FastSearch Windows service is not the one from this repo, or it is not creating the pipe (e.g. CreateNamedPipe failing).

**Pipe name (single source of truth):**

- Service (C++): `service\src\fastsearch_service.h` → `kPipeName` = `\\.\pipe\FastSearchMCP`
- Client (Python): `src\fastsearch_mcp\pipe_client.py` → `DEFAULT_PIPE_NAME`; override with env **`FASTSEARCH_PIPE_NAME`**

**Quick checks:**

1. Services: "FastSearchMCP" running? Path to exe = this repo’s `service\build\...\FastSearchServiceNew.exe`?
2. Event Log (source FastSearchMCP): "CreateNamedPipe failed" or "Service worker thread … started"?
3. Tests page: `pipe_connect` details show `error_code`, `error_message`, `pipe_name`.

**Resolution:** Reinstall service from this repo if path is wrong; fix CreateNamedPipe errors from Event Log; set `FASTSEARCH_PIPE_NAME` only if using a different pipe name.

**Full doc:** `docs\PIPE_CONNECTION_TROUBLESHOOTING.md`
