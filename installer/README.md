# FastSearch MCP Installer

This directory contains the installation package that:

1. **Installs the Windows Service** (`fastsearch-service.exe`)
   - Runs with elevated privileges for NTFS MFT access
   - Configured to start automatically
   - Creates named pipe server for IPC

2. **Installs the MCP Bridge** (`fastsearch-mcp-bridge.exe`)
   - User-mode MCP server for Claude Desktop
   - No UAC required during normal operation
   - Communicates with service via named pipes

3. **Registers the Service**
   - Windows service registration
   - Automatic startup configuration
   - Proper security context

## Installation Process

**One-time UAC Required**: Only during installation for:

- Installing Windows service with elevated privileges
- Setting up named pipe security
- Registering service for automatic startup

**Normal Operation**: No UAC prompts

- Bridge runs at user level
- Service runs as system service
- Claude Desktop integrates seamlessly

## Directory Structure

```
installer/
├── setup.iss          # Inno Setup script
├── install.ps1        # PowerShell installer
├── service-install.ps1 # Service registration
└── README.md          # This file
```
