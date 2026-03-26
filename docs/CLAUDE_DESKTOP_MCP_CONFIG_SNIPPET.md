# Claude Desktop MCP Configuration Snippet

## FastSearch MCP Configuration

Add this to your Claude Desktop MCP configuration file:

**Location**: 
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Configuration Snippet (Local Development)

**For local development** (when using the repo source directly):

```json
{
  "mcpServers": {
    "fastsearch-mcp": {
      "command": "python",
      "args": [
        "-m",
        "fastsearch_mcp"
      ],
      "cwd": "D:\\Dev\\repos\\fastsearch-mcp",
      "env": {
        "PYTHONPATH": "D:\\Dev\\repos\\fastsearch-mcp\\src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Note**: Replace `D:\\Dev\\repos\\fastsearch-mcp` with your actual repository path.

### Full Example (with other MCP servers)

```json
{
  "mcpServers": {
    "fastsearch-mcp": {
      "command": "python",
      "args": [
        "-m",
        "fastsearch_mcp"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    },
    "other-mcp-server": {
      "command": "python",
      "args": ["-m", "other_mcp"]
    }
  }
}
```

## Installation Methods

### Method 1: Manual Configuration

1. Open Claude Desktop
2. Go to Settings → Developer → Edit Config
3. Add the configuration snippet above
4. Save and restart Claude Desktop

### Method 2: MCPB Package (Recommended)

1. Build the MCPB package:
   ```powershell
   .\mcpb\scripts\build-mcpb-package.ps1 -NoSign
   ```

2. Install in Claude Desktop:
   - Drag and drop `dist/fastsearch-mcp-0.4.0.mcpb` into Claude Desktop
   - OR use: `mcpb install dist/fastsearch-mcp-0.4.0.mcpb`

3. Claude Desktop will automatically configure it

## Requirements

- Python 3.8+ installed
- FastSearch MCP package installed: `pip install -e .`
- FastSearch C++ service running (for full functionality)

## Verification

After configuration, you should see:
- FastSearch MCP server connected in Claude Desktop
- Tools available: `fastsearch.search`, `getStatus`, etc.
- Service status checkable via `getStatus` tool

## Troubleshooting

### Server Not Connecting

1. Check Python is in PATH: `python --version`
2. Verify package is installed: `pip list | findstr fastsearch`
3. Check Claude Desktop logs for errors

### Service Not Available

1. Check if FastSearch service is running:
   ```powershell
   Get-Service FastSearchMCP
   ```

2. Start the service if needed:
   ```powershell
   Start-Service FastSearchMCP
   ```

3. Use `fastsearch.search_basic` as fallback if service unavailable

## Environment Variables

The configuration includes:
- `cwd`: Working directory (your local repo path)
- `PYTHONPATH`: Points to the `src/` directory in your local repo
- `PYTHONUNBUFFERED`: Ensures real-time log output

**Note**: 
- **For local development**: Use the config above with your actual repo path
- **For MCPB packages**: Claude Desktop handles configuration automatically (no manual config needed)
- **For pip-installed packages**: Use `pip install -e .` and you can omit PYTHONPATH

## Related Documentation

- [MCPB Packaging Guide](mcpb-packaging/README.md)
- [Service Installation](../service/README.md)
- [Troubleshooting](../TROUBLESHOOTING.md)

