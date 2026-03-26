# FastSearch MCP - Pipe Connection Troubleshooting

**Problem:** Tests page or search reports "Named pipe not available or ping failed" with `connected: false`, often with **error 2** (pipe not found).

---

## What the pipe is

The Python MCP bridge talks to the FastSearch C++ Windows service over a **named pipe**. The service creates the pipe; the client connects to it. If the pipe does not exist when the client calls `CreateFile`, Windows returns **error 2** (ERROR_FILE_NOT_FOUND).

---

## Where the pipe name is defined

The pipe path must match on both sides:

| Side    | File                                  | Symbol / constant      | Value (Windows)        |
|---------|----------------------------------------|------------------------|--------------------------|
| Service | `service\src\fastsearch_service.h`     | `kPipeName`            | `L"\\\\.\\pipe\\FastSearchMCP"` |
| Client  | `src\fastsearch_mcp\pipe_client.py`    | `DEFAULT_PIPE_NAME`, `get_pipe_name()` | `r"\\.\pipe\FastSearchMCP"`     |

`service_client.py` imports `get_pipe_name()` from `pipe_client` for availability checks and status payloads. Keep the pipe string defined only in `pipe_client.py` (no duplicate constants elsewhere).

Same logical name: **`\\.\pipe\FastSearchMCP`**. If you use a different build or fork, set the client via **env `FASTSEARCH_PIPE_NAME`** (e.g. `\\.\pipe\YourPipeName`).

---

## Why "pipe not found" (error 2) happens

1. **Wrong service running**  
   The process shown in Windows Services as "FastSearchMCP" might be a different executable (other installer, older build) that does **not** create `\\.\pipe\FastSearchMCP`.

2. **Service not from this repo**  
   Only the service built from this repo (`service\src\fastsearch_service.cpp` and same `kPipeName`) creates that pipe. Any other binary may use another pipe name or no pipe.

3. **Service failed to create the pipe**  
   The service starts but `CreateNamedPipe` fails (e.g. permissions, or all instances busy). The pipe then never exists, so the client gets error 2.

4. **Service not running**  
   If the service is stopped, no process creates the pipe, so the client gets error 2.

---

## Diagnosis steps

1. **Confirm service is running**  
   - `services.msc` → find "FastSearch MCP" / "FastSearchMCP".  
   - Status should be "Running".

2. **Confirm executable path**  
   - In `services.msc`: right‑click the service → Properties → "Path to executable".  
   - Should point to the exe from **this repo**, e.g.  
     `D:\Dev\repos\fastsearch-mcp\service\build\bin\Release\FastSearchServiceNew.exe`.  
   - If it points elsewhere, the running service is not the one from this repo.

3. **Check Windows Event Log**  
   - Event Viewer → Windows Logs → Application (or where your service logs).  
   - Filter by source **FastSearchMCP**.  
   - Look for:
     - "Service worker thread … started" → worker threads started; pipe creation is attempted.
     - "CreateNamedPipe failed with error …" → pipe creation failed (use the error code to look up cause).
     - "Client connected to named pipe" → pipe exists and at least one client connected.

4. **Use the Tests page diagnostics**  
   - Webapp → **Tests** → Run tests.  
   - In **pipe_connect** details you get:
     - `error_code` (e.g. 2 = not found, 5 = access denied)
     - `error_message` (Windows text)
     - `pipe_name` (the path the client used)

---

## Fixes

| Cause                         | Action |
|------------------------------|--------|
| Service not running          | Start the service (e.g. `services.msc` → Start, or `start_service` tool). |
| Wrong executable / not this repo | Reinstall the service from this repo: run `service\install_service.ps1` (or your install script) so the correct `FastSearchServiceNew.exe` is registered. |
| CreateNamedPipe failing in Event Log | Resolve the reported error (e.g. permissions, duplicate name). Restart the service after fixing. |
| Different pipe name in your build | Set **`FASTSEARCH_PIPE_NAME`** in the environment for the process that runs the MCP bridge/webapp to the pipe name your service uses. |

---

## Error codes (client CreateFile)

| Code | Meaning           | Typical cause |
|------|-------------------|----------------|
| 2    | File not found    | Pipe does not exist (service not creating it, or wrong service). |
| 5    | Access denied     | Permissions or ACLs; client and service may run as different users. |
| 231  | All pipe instances busy | Service at capacity; retry shortly. |

---

## References

- Pipe name in service: `service\src\fastsearch_service.h` (`kPipeName`).
- Client default and env override: `src\fastsearch_mcp\pipe_client.py` (`get_pipe_name()`, `DEFAULT_PIPE_NAME`, `FASTSEARCH_PIPE_NAME`).
- Service availability and checks: `docs\SERVICE_AVAILABILITY_CHECKS.md`.
- Live tests and diagnostics: webapp **Tests** page, `src\fastsearch_mcp\live_tests.py`.
