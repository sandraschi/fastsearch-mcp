# FastSearch MCP Release Packaging

## Two-Package Strategy

FastSearch MCP uses a **dual-package architecture** for release:

### Package 1: MSI Installer (Windows Service)

**File**: `fastsearch-mcp-setup.msi`  
**Purpose**: Installs the C++ Windows service  
**Requires**: Administrator privileges (UAC)  
**Contains**:
- `FastSearchServiceNew.exe` (C++ service binary)
- Service installation scripts
- Windows Event Log registration
- Automatic service startup

**Build**: WiX Toolset (free, open-source)

### Package 2: MCPB Package (Claude Desktop Extension)

**File**: `fastsearch-mcp-0.5.0.mcpb`  
**Purpose**: Claude Desktop MCP extension  
**Requires**: User-level permissions only  
**Contains**:
- Python MCP bridge source code
- `manifest.json` (runtime configuration)
- `requirements.txt` (dependencies - installed by Claude Desktop)
- `prompts/` (prompt templates)

**Build**: MCPB CLI (`mcpb pack`)

## Build Process

### Automated (GitHub Actions)

The `.github/workflows/build-release.yml` workflow automatically:

1. Builds MSI installer (Windows)
2. Builds MCPB package (Windows/Linux/macOS)
3. Creates GitHub Release
4. Uploads both packages

### Manual Build

```powershell
# 1. Build MSI installer
cd installer
.\build_installer.ps1

# 2. Build MCPB package
.\mcpb\scripts\build-mcpb-package.ps1 -NoSign

# Output:
# - dist/fastsearch-mcp-setup.msi
# - dist/fastsearch-mcp-0.5.0.mcpb
```

## Release Structure

```
GitHub Release: v0.5.0
├── fastsearch-mcp-setup.msi          # ⚠️ REQUIRES UAC
├── fastsearch-mcp-0.5.0.mcpb         # ✅ User-level
├── fastsearch-mcp-0.5.0.zip          # Source code
└── RELEASE_NOTES.md                  # Installation guide
```

## Installation Order

**CRITICAL**: Users must install in this order:

1. **First**: Install MSI (elevated)
   - Right-click → Run as Administrator
   - Installs and starts service

2. **Second**: Install MCPB (user-level)
   - Drag into Claude Desktop
   - Claude Desktop installs dependencies
   - Connects to service

## Why Two Packages?

### Technical Reasons

- **Service requires elevation**: NTFS MFT access needs `LocalSystem` privileges
- **MCPB is user-level**: Claude Desktop extensions run in user context
- **Security separation**: Service runs elevated, bridge runs as user

### User Experience

- **Clear separation**: Users understand what requires admin
- **Flexible installation**: Can install MCPB without service (fallback mode)
- **Standard patterns**: MSI for system services, MCPB for extensions

## Release Notes Template

```markdown
# FastSearch MCP v0.5.0

## Installation

FastSearch MCP requires a two-step installation:

### Step 1: Install Windows Service (Requires Administrator)

1. Download `fastsearch-mcp-setup.msi`
2. Right-click → **Run as Administrator**
3. Follow the installation wizard
4. Service will start automatically

### Step 2: Install Claude Desktop Extension

1. Download `fastsearch-mcp-0.5.0.mcpb`
2. Open Claude Desktop
3. Drag and drop the `.mcpb` file
4. Done!

## What's Included

- **fastsearch-mcp-setup.msi**: Windows service installer (requires UAC)
- **fastsearch-mcp-0.5.0.mcpb**: Claude Desktop extension (user-level)
- **fastsearch-mcp-0.5.0.zip**: Source code

## System Requirements

- Windows 10/11 (64-bit)
- Administrator account (for service installation)
- Python 3.8+ (installed automatically)
- Claude Desktop 1.0+

## Troubleshooting

See [Installation Guide](docs/RELEASE_INSTALLATION.md) for detailed troubleshooting.
```

## Related Documentation

- [Release Installation Guide](RELEASE_INSTALLATION.md)
- [MCPB Packaging](mcpb-packaging/README.md)
- [Service Installation](../service/README.md)

