# FastSearch MCP Service

This directory contains the FastSearch MCP C++ Windows Service implementation.

## Architecture & Privilege Separation Model

FastSearch MCP employs a strict zero-overhead **Privilege Separation Architecture** (modeled after WizFile / Voidtools Everything):

```text
┌─────────────────────────────────────────────────────────┐
│ Elevated Kernel / Service Domain (Installed ONCE)       │
│ - FastSearchMCP Windows Service (LocalSystem / Admin)   │
│ - Reads raw NTFS MFT volume structures (\\.\C:, \\.\D:) │
│ - Listens on IPC Named Pipe (\\.\pipe\FastSearchMCP)    │
└────────────────────────────┬────────────────────────────┘
                             │ IPC Named Pipe
┌────────────────────────────┴────────────────────────────┐
│ Unprivileged User Domain (Standard User Space)          │
│ - Python MCP Server / REST API Bridge / Web UI           │
│ - Zero elevation required at runtime                    │
│ - Connects via Win32 Named Pipe client                  │
└─────────────────────────────────────────────────────────┘
```

1. **Elevated Windows Service (`LocalSystem` / Admin)**:
   - Installed **ONCE** as a background Windows Service (`FastSearchMCP`).
   - Holds kernel/admin privileges necessary to open raw volume handles (`\\.\C:`, `\\.\D:`) for instant, zero-indexing MFT parses.
   - Listens on IPC named pipe `\\.\pipe\FastSearchMCP`.

2. **Unprivileged Client (Standard User)**:
   - The Python MCP server, REST API bridge, and Web UI run completely in **standard user space**.
   - Requires **zero administrator privileges or UAC prompts** during runtime search operations.
   - Connects over named pipe `\\.\pipe\FastSearchMCP`, sends search JSON requests, and receives MFT search results back.

## Prerequisites

- Windows 10/11 or Windows Server 2016+
- CMake 3.20+ & C++17 compiler (MSVC 2019/2022)
- Administrator privileges for service installation

## Building the Service

Build the C++ service executable via Just or CMake:
```powershell
just build-service
# or
cd service/build
cmake --build . --config Release
```

## Installing & Starting the Service

To install and start the service (run once as Administrator):
```powershell
just install-service
# or elevated PowerShell:
Start-Service FastSearchMCP
```

## Managing the Service

- **Start**: `sc start FastSearchMCP` or `Start-Service FastSearchMCP`
- **Stop**: `sc stop FastSearchMCP` or `Stop-Service FastSearchMCP`
- **Check Status**: `sc query FastSearchMCP` or `just status`

## Service Details

- **Service Name**: `FastSearchMCP`
- **Display Name**: `FastSearch MCP Service`
- **Pipe Name**: `\\.\pipe\FastSearchMCP`
- **Executable**: `service/build/bin/Release/FastSearchServiceNew.exe`

## Troubleshooting

- If named pipe connection fails, verify the Windows Service is installed and running (`sc query FastSearchMCP`).
- Ensure the service is running as `LocalSystem` so it has direct MFT volume read permissions.
- Inspect logs via `just logs` or `GET /api/logs`.
