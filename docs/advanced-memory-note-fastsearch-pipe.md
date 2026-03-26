---
title: FastSearch MCP pipe_connect failure (error 2)
tags:
  - fastsearch-mcp
  - troubleshooting
  - windows
  - named-pipe
created: 2025-03-04
---

# FastSearch MCP pipe_connect failure (error 2)

- [symptom] Tests page or search reports "Named pipe not available or ping failed"; pipe_connect shows connected: false, often error 2 (ERROR_FILE_NOT_FOUND).
- [cause] The named pipe \\.\pipe\FastSearchMCP does not exist when the client connects: wrong Windows service exe, service not creating the pipe, or service not running.
- [definition] Pipe name is defined in service at service\src\fastsearch_service.h (kPipeName) and in client at src\fastsearch_mcp\pipe_client.py (DEFAULT_PIPE_NAME); override with env FASTSEARCH_PIPE_NAME.
- [diagnosis] Confirm FastSearchMCP service is running; check Path to executable in services.msc matches this repo (e.g. service\build\...\FastSearchServiceNew.exe); check Event Log source FastSearchMCP for "CreateNamedPipe failed" or "Service worker thread … started"; use Tests page pipe_connect details for error_code, error_message, pipe_name.
- [resolution] Start service if stopped; reinstall service from this repo if wrong exe; fix CreateNamedPipe errors from Event Log; set FASTSEARCH_PIPE_NAME only if using a different pipe name.
- [reference] Full troubleshooting: fastsearch-mcp docs\PIPE_CONNECTION_TROUBLESHOOTING.md; service checks: docs\SERVICE_AVAILABILITY_CHECKS.md; ops note: docs\STATUS_NOTE_MEMOPS.md.
