# FastSearch MCP C++ Service Implementation

## Overview

The FastSearch MCP service is a minimal Windows service written in C++17. Its sole responsibility is to respond to search requests by streaming results directly from the NTFS Master File Table (MFT). The service performs no background indexing, caching, or directory walking.

---

## Key Characteristics

- **Direct NTFS access:** uses Windows APIs and the `ntfs` support library to enumerate MFT records live.
- **On-demand processing:** the service wakes only when the named pipe receives a request and shuts down the scan as soon as `max_results` is satisfied.
- **Privilege separation:** runs as `LocalSystem`, while the Python bridge runs unprivileged. All IPC happens through `\\.\pipe\FastSearchMCP`.
- **Structured diagnostics:** every critical step logs to the Windows Event Log to aid debugging (especially Event ID 7034 crashes).
- **No caching:** results are streamed immediately. Any suggestion to add caches or precomputed indexes must be rejected.

---

## Service Entry Point

```cpp
int wmain(int argc, wchar_t* argv[]) {
    FastSearchService service;

    if (argc > 1) {
        return HandleCommandLine(argc, argv, service); // install/uninstall/debug
    }

    SERVICE_TABLE_ENTRY service_table[] = {
        { SERVICE_NAME, ServiceMain },
        { nullptr, nullptr }
    };

    if (!StartServiceCtrlDispatcher(service_table)) {
        SvcLogMessage(EventLogLevel::Error, L"StartServiceCtrlDispatcher failed", GetLastError());
    }
    return 0;
}
```

- `HandleCommandLine` supports `--install`, `--uninstall`, and `--debug` for manual testing.
- In service mode we register control handlers, initialise logging, and spin up the worker thread that listens on the named pipe.

---

## Named Pipe Listener

```cpp
void FastSearchService::Run() {
    while (!shutdown_requested_) {
        PipeServer pipe(pipe_name_);
        if (!pipe.WaitForClient(connect_timeout_)) {
            continue; // Loop until a client connects
        }

        auto request = pipe.ReadRequest();
        if (!request) {
            continue;
        }

        ProcessRequest(*request, pipe);
    }
}
```

- The pipe is created with security descriptors that restrict access to the active user session.
- Messages are newline-delimited JSON. Each response is streamed as a sequence of JSON frames so the bridge can start rendering results immediately.

---

## Processing a Search Request

```cpp
void FastSearchService::ProcessRequest(const SearchRequest& req, PipeServer& pipe) {
    auto volume = OpenVolume(req.drive);
    if (!volume) {
        pipe.SendError(req.id, L"Failed to open volume", volume.error());
        return;
    }

    NtfsScanner scanner(volume.value());
    PatternMatcher matcher(req.pattern, req.path_filter);

    size_t emitted = 0;
    for (const auto& record : scanner) {
        if (!matcher.Matches(record)) {
            continue;
        }

        pipe.SendResult(req.id, record.ToDto());
        if (++emitted >= req.max_results) {
            break; // hard stop honours architecture rules
        }
    }

    pipe.SendComplete(req.id, emitted);
}
```

- `NtfsScanner` lazily iterates MFT records with buffers sized for streaming.
- `PatternMatcher` optimises literal matches and uses compiled regex only when necessary.
- Results are translated into lightweight DTO structs (`path`, `size`, timestamps, attributes) before serialisation.

---

## Error Handling & Logging

```cpp
void SvcLogMessage(EventLogLevel level, const std::wstring& message, DWORD error) {
    const wchar_t* strings[] = { message.c_str() };
    ReportEventW(
        event_source_,
        static_cast<WORD>(level),
        0,
        BASE_EVENT_ID + static_cast<DWORD>(level),
        nullptr,
        1,
        sizeof(error),
        strings,
        &error);
}
```

Key checkpoints that log `Information` or `Error` events:
1. Service control registration
2. Privilege escalation attempts (`SeBackupPrivilege`)
3. Named pipe creation and connection
4. Volume handle acquisition
5. Search completion or failure

Logs are read via `scripts/read-service-logs.ps1` or the Windows Event Viewer (`Applications and Services Logs/FastSearchMCP`).

---

## Building the Service

### Prerequisites
- Visual Studio 2022 (Build Tools or full IDE)
- Windows 10/11 SDK
- CMake 3.20+

### Steps

```powershell
cd service
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
```

The resulting binary lives at `service\build\bin\Release\FastSearchServiceNew.exe`.

---

## Installing / Managing the Service

```powershell
# Elevated PowerShell
.\install-service.ps1 install
.\install-service.ps1 start
.\install-service.ps1 status

# Cleanup
.\install-service.ps1 stop
.\install-service.ps1 uninstall
```

Troubleshooting scripts:
- `debug-service-startup.ps1` – validates privileges, paths, registry entries, and event logs.
- `test-service-comprehensive.ps1` – automated smoke tests for install/start/log/pipe connectivity.
- `capture-service-debug.ps1` – optional live tracing for development (never enabled by default).

---

## Current Focus Areas

1. **Startup stability:** resolving the Event ID 7034 crash observed on some machines. Enhanced logging has been added around privilege enablement and pipe initialisation.
2. **Pipe contract hardening:** ensuring back-pressure and error frames are handled gracefully when the bridge disconnects mid-search.
3. **Integration testing:** end-to-end tests that require elevation are being expanded; see `tests/test_fastsearch.py`.

---

The service must remain lean. Any proposal to add indexing, caching, or long-lived data structures contradicts the core FastSearch value proposition and must be rejected.
