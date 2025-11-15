# FastSearch MCP Installation Methods

FastSearch MCP supports **three installation methods** depending on your use case:

## 1. Local Installation (Development)

**Use Case**: Development, contributing, custom builds

### Prerequisites

- Windows 10/11 with NTFS volumes
- Administrator account (for service installation)
- Python 3.8+ with `pip`
- Git
- Visual Studio 2022 Build Tools (or full VS) for C++ service
- CMake 3.20+

### Installation Steps

```powershell
# 1. Clone repository
git clone https://github.com/sandraschi/fastsearch-mcp.git
cd fastsearch-mcp

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install Python dependencies
pip install -r requirements-dev.txt
pip install -e .

# 4. Build C++ service
cd service
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
cd ..

# 5. Install Windows service (requires admin)
.\service\build\bin\Release\FastSearchServiceNew.exe install
Start-Service FastSearchMCP

# 6. Run MCP server
python -m fastsearch_mcp
```

### Configuration

Add to your IDE's MCP config (Cursor/Windsurf/Zed):

```json
{
  "mcpServers": {
    "fastsearch-mcp": {
      "command": "python",
      "args": ["-m", "fastsearch_mcp"],
      "cwd": "D:\\Dev\\repos\\fastsearch-mcp",
      "env": {
        "PYTHONPATH": "D:\\Dev\\repos\\fastsearch-mcp\\src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## 2. NPX Installation (IDEs: Cursor, Windsurf, Zed)

**Use Case**: Quick installation for IDEs that support MCP

### Prerequisites

- Node.js 16+ (for NPX)
- Python 3.8+ installed and in PATH
- Administrator account (for service installation - one-time)

### Installation Steps

```powershell
# 1. Install Windows service (requires admin - one-time setup)
# Download and run: fastsearch-mcp-setup.msi
# OR build and install manually (see Local Installation)

# 2. Install Python package (if not already installed)
pip install fastsearch-mcp

# 3. Use via NPX in IDE config
```

### Configuration

**Cursor IDE** (`%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`):

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

**Windsurf IDE** (`%APPDATA%\Windsurf\mcp.json`):

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

**Zed IDE** (`%APPDATA%\Zed\settings.json`):

```json
{
  "mcp": {
    "servers": {
      "fastsearch-mcp": {
        "command": "npx",
        "args": ["-y", "fastsearch-mcp"]
      }
    }
  }
}
```

### How It Works

- NPX downloads and runs `fastsearch-mcp` package
- The `bin/fastsearch-mcp.js` script launches Python MCP server
- Python dependencies must be installed: `pip install fastsearch-mcp`
- Service must be running for full functionality

## 3. MCPB Package (Claude Desktop Only)

**Use Case**: Claude Desktop users

### Prerequisites

- Claude Desktop 1.0+
- Python 3.8+ (installed automatically by Claude Desktop)
- Administrator account (for service installation - one-time)

### Installation Steps

#### Step 1: Install Windows Service (Requires UAC)

**Option A: MSI Installer (Recommended)**

1. Download `fastsearch-mcp-setup.msi` from GitHub Releases
2. Right-click → **Run as Administrator**
3. Follow the installation wizard
4. Service will be installed and started automatically

**Option B: Manual Installation**

```powershell
# Build the service
cd service
cmake --build build --config Release

# Install service (requires admin)
cd build\bin\Release
.\FastSearchServiceNew.exe install
Start-Service FastSearchMCP
```

#### Step 2: Install MCPB Package

**Option A: Drag & Drop (Easiest)**

1. Download `fastsearch-mcp-0.4.0.mcpb` from GitHub Releases
2. Open Claude Desktop
3. Drag and drop the `.mcpb` file into Claude Desktop
4. Claude Desktop will:
   - Extract the package
   - Install Python dependencies from `requirements.txt`
   - Configure the MCP server
   - Connect to the service

**Option B: MCPB CLI**

```powershell
# Install MCPB CLI (if not already installed)
npm install -g @anthropic-ai/mcpb

# Install the package
mcpb install fastsearch-mcp-0.4.0.mcpb
```

### Configuration

MCPB package automatically configures Claude Desktop. No manual configuration needed.

## Service Installation (Required for All Methods)

The C++ Windows service **must be installed** for full functionality (direct NTFS MFT access).

### One-Time Service Setup

```powershell
# Option 1: MSI Installer (easiest)
# Download fastsearch-mcp-setup.msi and run as Administrator

# Option 2: Manual installation
cd service\build\bin\Release
.\FastSearchServiceNew.exe install
Start-Service FastSearchMCP
```

### Verify Service

```powershell
# Check service status
Get-Service FastSearchMCP

# Check service logs
Get-EventLog -LogName Application -Source FastSearchMCP -Newest 10
```

## Fallback Mode

If the service is not available, FastSearch MCP will:
- Use `fastsearch.search_basic` (slower, standard filesystem traversal)
- Show warnings that direct MFT access is unavailable
- Provide instructions to install the service

## Comparison Table

| Method | Use Case | Service Install | Python Install | IDE Support |
|--------|----------|----------------|----------------|-------------|
| **Local** | Development | Manual | `pip install -e .` | All (manual config) |
| **NPX** | Quick IDE setup | One-time (MSI) | `pip install fastsearch-mcp` | Cursor, Windsurf, Zed |
| **MCPB** | Claude Desktop | One-time (MSI) | Auto (by Claude Desktop) | Claude Desktop only |

## Troubleshooting

### Service Not Available

**Symptom**: `fastsearch.search` returns "service not available"

**Solution**:
1. Install the service: `fastsearch-mcp-setup.msi` (Run as Administrator)
2. Verify: `Get-Service FastSearchMCP`
3. Start if needed: `Start-Service FastSearchMCP`

### NPX Installation Issues

**Symptom**: NPX can't find Python or module

**Solution**:
1. Verify Python: `python --version`
2. Install package: `pip install fastsearch-mcp`
3. Check PATH includes Python

### MCPB Package Issues

**Symptom**: Claude Desktop shows "server disconnected"

**Solution**:
1. Check Python: `python --version`
2. Check dependencies: `pip list | findstr fastsearch`
3. Reinstall MCPB package
4. Check Claude Desktop logs

## Related Documentation

- [Release Installation](RELEASE_INSTALLATION.md)
- [Service Installation](../service/README.md)
- [MCPB Packaging](mcpb-packaging/README.md)
- [Troubleshooting](../TROUBLESHOOTING.md)

