# FastSearch MCP - Installation Guide

FastSearch MCP consists of a privileged C++ Windows service and an unprivileged Python MCP bridge. Follow the steps below to build, install, and verify the stack on Windows.

## Prerequisites

- Windows 10/11 (64-bit) with NTFS volumes
- Administrator access (required once to install the service)
- [Python 3.10+](https://www.python.org/downloads/)
- [Visual Studio 2022 Build Tools](https://aka.ms/vs/17/release/vs_BuildTools.exe) with the **Desktop development with C++** workload
- [CMake 3.20+](https://cmake.org/download/)
- [WiX Toolset v3.11+](https://wixtoolset.org/releases/) (only if you plan to build an MSI installer)

> **Note:** Ensure `cmake`, `python`, and the Visual Studio build tools are available in your `PATH` before continuing.

## Build the Project

### 1. Clone the Repository

```powershell
git clone https://github.com/yourusername/fastsearch-mcp.git
cd fastsearch-mcp
```

### 2. Set Up the Python Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pip install -e .
```

### 3. Build the C++ Service

```powershell
cd service
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
cd ..
```

The compiled service binary is generated at `service\build\bin\Release\FastSearchServiceNew.exe`.

## Install and Manage the Service

### Install (Requires Elevated PowerShell)

```powershell
.\install-service.ps1 install
```

### Start / Stop / Status

```powershell
.\install-service.ps1 start
.\install-service.ps1 status
.\install-service.ps1 stop
```

### Uninstall

```powershell
.\install-service.ps1 uninstall
```

> Use `.\install-service.ps1 diagnose` or `.\debug-service-startup.ps1` whenever the service fails to start. These scripts collect event logs, check privileges, and highlight missing dependencies.

## Run the MCP Bridge (User Mode)

With the virtual environment activated:

```powershell
python scripts/start_server.py
```

Claude Desktop can now attach to FastSearch MCP using the command defined in `mcp.config.json`.

## Troubleshooting

| Symptom | Suggested Action |
|---------|------------------|
| Service fails immediately with Event ID 7034 | Run `.\debug-service-startup.ps1 -Verbose` to display each initialisation step and consult the Windows Event Viewer (`Applications and Services Logs → FastSearchMCP`). |
| Bridge reports “service unavailable” | Confirm the service is running (`.\install-service.ps1 status`) and that the named pipe `\\.\pipe\FastSearchMCP` exists. |
| “Access denied” errors when opening volumes | Verify the service is installed under `LocalSystem` and that the process has `SeBackupPrivilege`. Reinstall from an elevated shell if necessary. |
| Python fallback is always used | Ensure the service is running and reachable; the bridge falls back when the pipe handshake fails or the service returns an error response. |

## Optional: Build the MSI Installer

If you need a distributable installer:

```powershell
.\create-installer.ps1 -Version <version>
```

The generated MSI is placed in the `dist` directory.

## Support

For additional help, open an issue on the [GitHub repository](https://github.com/yourusername/fastsearch-mcp/issues) or follow the diagnostic workflow in `docs/SERVICE_IMPROVEMENTS.md`.
