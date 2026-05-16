# FastSearch MCP Release Installation Guide

## Overview

FastSearch MCP supports **three installation methods**:

1. **Local Installation** - Git clone for development
2. **NPX Installation** - For Cursor IDE, Windsurf IDE, Zed IDE, etc.
3. **MCPB Package** - For Claude Desktop only

All methods require the **Windows Service** to be installed first (one-time, requires UAC).

## Installation Methods

See [Installation Methods Guide](INSTALLATION_METHODS.md) for detailed instructions for each method.

## Quick Start

### For Claude Desktop Users

1. **Install Service** (requires admin):
   - Download `fastsearch-mcp-setup.msi`
   - Right-click → Run as Administrator

2. **Install Extension**:
   - Download `fastsearch-mcp-0.5.0.mcpb`
   - Drag into Claude Desktop

### For IDE Users (Cursor, Windsurf, Zed)

1. **Install Service** (requires admin):
   - Download `fastsearch-mcp-setup.msi`
   - Right-click → Run as Administrator

2. **Install Python Package**:
   ```powershell
   pip install fastsearch-mcp
   ```

3. **Configure IDE**:
   ```json
   {
     "mcpServers": {
       "fastsearch-mcp": {
         "command": "npx",
         "args": ["-y", "fastsearch-mcp"]
       }
     }
   }
   ```

### For Developers

See [Local Installation](INSTALLATION_METHODS.md#1-local-installation-development) section.

## Service Installation (Required for All Methods)

**IMPORTANT**: The Windows service must be installed first for full functionality.

### Step 1: Install Windows Service (Requires UAC)

#### Option A: MSI Installer (Recommended for Release)

1. Download `fastsearch-mcp-setup.msi` from GitHub Releases
2. Right-click → **Run as Administrator**
3. Follow the installation wizard
4. Service will be installed and started automatically

#### Option B: Manual Installation

```powershell
# Build the service
cd service
cmake --build build --config Release

# Install service (requires admin)
cd build\bin\Release
.\FastSearchServiceNew.exe install

# Start service
Start-Service FastSearchMCP
```

### Step 2: Install MCPB Package (User-Level)

#### Option A: Drag & Drop (Easiest)

1. Download `fastsearch-mcp-0.5.0.mcpb` from GitHub Releases
2. Open Claude Desktop
3. Drag and drop the `.mcpb` file into Claude Desktop
4. Claude Desktop will:
   - Extract the package
   - Install Python dependencies from `requirements.txt`
   - Configure the MCP server
   - Connect to the service

#### Option B: MCPB CLI

```powershell
# Install MCPB CLI (if not already installed)
npm install -g @anthropic-ai/mcpb

# Install the package
mcpb install fastsearch-mcp-0.5.0.mcpb
```

## Release Package Structure

GitHub Releases will contain:

```
fastsearch-mcp-v0.5.0/
├── fastsearch-mcp-setup.msi          # Windows Service Installer (REQUIRES UAC)
├── fastsearch-mcp-0.5.0.mcpb         # Claude Desktop Extension (user-level)
├── fastsearch-mcp-0.5.0.zip          # Source code archive
└── README.md                          # Installation instructions
```

## Installation Verification

### Check Service Status

```powershell
# Check if service is running
Get-Service FastSearchMCP

# Check service logs
Get-EventLog -LogName Application -Source FastSearchMCP -Newest 10
```

### Check MCP Connection

1. Open Claude Desktop
2. Check Settings → MCP Servers
3. Verify `fastsearch-mcp` is connected
4. Test with: "Check FastSearch service status"

## Troubleshooting

### Service Not Installed

**Symptom**: `fastsearch.search` returns "service not available"

**Solution**:
1. Install the MSI: `fastsearch-mcp-setup.msi` (Run as Administrator)
2. Verify service: `Get-Service FastSearchMCP`
3. Start if needed: `Start-Service FastSearchMCP`

### MCPB Package Not Working

**Symptom**: Claude Desktop shows "server disconnected"

**Solution**:
1. Check Python is installed: `python --version`
2. Check dependencies: `pip list | findstr fastsearch`
3. Reinstall MCPB package
4. Check Claude Desktop logs

### Access Denied Errors

**Symptom**: Named pipe connection fails

**Solution**:
1. Service must be running as `LocalSystem`
2. Verify service installation: `sc qc FastSearchMCP`
3. Reinstall service if needed

## Fallback Mode

If the service is not available, FastSearch MCP will:
- Use `fastsearch.search_basic` (slower, standard filesystem traversal)
- Show warnings that direct MFT access is unavailable
- Provide instructions to install the service

## Uninstallation

### Uninstall Service

```powershell
# Stop service
Stop-Service FastSearchMCP

# Uninstall service
cd "C:\Program Files\FastSearchMCP"
.\FastSearchServiceNew.exe uninstall
```

Or use Windows Settings → Apps → FastSearch MCP Service → Uninstall

### Uninstall MCPB Package

1. Open Claude Desktop
2. Settings → MCP Servers
3. Remove `fastsearch-mcp`
4. Delete package directory (if needed)

## Release Checklist

Before releasing:

- [ ] MSI installer builds successfully
- [ ] MSI installer requires UAC (perMachine install)
- [ ] Service installs and starts automatically
- [ ] MCPB package builds successfully
- [ ] MCPB package installs without errors
- [ ] Service and MCPB communicate correctly
- [ ] Installation instructions are clear
- [ ] Both packages are in GitHub Release

## User Instructions (Release Notes)

### Quick Start

1. **Install Service** (requires admin):
   - Download `fastsearch-mcp-setup.msi`
   - Right-click → Run as Administrator
   - Follow the wizard

2. **Install Extension**:
   - Download `fastsearch-mcp-0.5.0.mcpb`
   - Drag into Claude Desktop
   - Done!

### System Requirements

- Windows 10/11 (64-bit)
- Administrator account (for service installation)
- Python 3.8+ (installed automatically by MCPB)
- Claude Desktop 1.0+

## Related Documentation

- [Service Installation](../service/README.md)
- [MCPB Packaging](mcpb-packaging/README.md)
- [Troubleshooting](../TROUBLESHOOTING.md)

