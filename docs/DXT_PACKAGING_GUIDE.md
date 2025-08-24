# FastSearchMCP DXT Packaging Guide

## Overview

This document outlines the process for packaging the FastSearchMCP components for distribution. Due to its architecture with an elevated Windows service, the packaging process is more complex than a standard MCP package.

## Architecture

FastSearchMCP consists of two main components:

1. **FastSearch Service** (`fastsearch-service.exe`)
   - Runs as a Windows service with elevated privileges
   - Handles direct NTFS Master File Table access
   - Communicates with the bridge via named pipes

2. **MCP Bridge** (`fastsearch-mcp-bridge.exe`)
   - Runs in user context
   - Implements the MCP protocol for Claude Desktop
   - Forwards requests to the service via named pipes

## Packaging Strategy

Due to the elevated privileges required by the service, we use a two-part packaging approach:

1. **Windows Installer (MSI)** - For the service component
2. **DXT Package** - For the MCP bridge component

## Part 1: Building the Service Installer

### Prerequisites

- WiX Toolset v3.11 or later
- Rust toolchain (for building the service)
- PowerShell 5.1 or later

### Building the Installer

1. Open a PowerShell console as Administrator
2. Navigate to the installer directory:
   ```powershell
   cd d:\Dev\repos\fastsearch-mcp\installer
   ```
3. Run the build script:
   ```powershell
   .\build_installer.ps1
   ```
4. The installer will be created at `d:\Dev\repos\fastsearch-mcp\dist\FastSearchMCP-Setup.msi`

### Installation

1. Right-click the MSI file and select "Run as administrator"
2. Follow the installation wizard
3. The service will be installed and started automatically

## Part 2: Creating the DXT Package

### Prerequisites

- DXT CLI tool
- Python 3.8 or later

### Building the DXT Package

1. Build the bridge component:
   ```powershell
   cd d:\Dev\repos\fastsearch-mcp\bridge
   cargo build --release
   ```

2. Create a directory for the DXT package:
   ```powershell
   $dxtDir = "d:\Dev\repos\fastsearch-mcp\dxt-package"
   New-Item -ItemType Directory -Path $dxtDir -Force
   ```

3. Copy the bridge binary:
   ```powershell
   Copy-Item "d:\Dev\repos\fastsearch-mcp\bridge\target\release\fastsearch-mcp-bridge.exe" -Destination $dxtDir
   ```

4. Create a `manifest.json` file in the DXT directory:
   ```json
   {
     "name": "fastsearch-mcp-bridge",
     "version": "1.0.0",
     "dxt_version": "1.0.0",
     "description": "MCP bridge for FastSearch NTFS file search service",
     "author": {
       "name": "Your Name",
       "email": "your.email@example.com",
       "url": "https://example.com"
     },
     "license": "MIT",
     "server": {
       "type": "executable",
       "entry_point": "fastsearch-mcp-bridge.exe",
       "mcp_config": {
         "command": "./fastsearch-mcp-bridge.exe"
       }
     },
     "prompts": [
       {
         "name": "search_files_prompt",
         "description": "Search for files matching a pattern",
         "text": "Search for files matching {pattern} in {directory}"
       },
       {
         "name": "find_file_prompt",
         "description": "Find a specific file by name",
         "text": "Find file named {filename} in {directory}"
       },
       {
         "name": "search_content_prompt",
         "description": "Search for files containing specific text",
         "text": "Find files containing {text} in {directory}"
       }
     ]
   }
   ```

5. Build the DXT package:
   ```powershell
   cd $dxtDir
   dxt pack
   ```

## Installation Order

1. First, install the MSI package (elevated privileges required)
2. Then, install the DXT package in Claude Desktop

## Troubleshooting

### Service Not Starting
- Verify the service is installed: `Get-Service -Name "FastSearchService"`
- Check the Windows Event Viewer for error messages
- Ensure the service account has the necessary permissions

### Bridge Cannot Connect to Service
- Verify the service is running
- Check the named pipe: `\\.\pipe\fastsearch-mcp`
- Ensure the user account has permission to access the named pipe

### DXT Package Fails to Load
- Verify the manifest.json is valid
- Check that the bridge executable is in the package
- Ensure the entry point in the manifest matches the executable name

## Security Considerations

- The service runs with elevated privileges - only install from trusted sources
- Named pipe communication is secured with appropriate ACLs
- The bridge runs with user privileges and cannot elevate on its own

## Maintenance

### Updating the Service
1. Build the new service binary
2. Update the MSI package version
3. Distribute the updated MSI

### Updating the Bridge
1. Build the new bridge binary
2. Update the DXT package version
3. Distribute the updated DXT package

## Uninstallation

1. Uninstall the DXT package from Claude Desktop
2. Uninstall the MSI package using Add/Remove Programs

---
*Document generated on 2025-08-02*
