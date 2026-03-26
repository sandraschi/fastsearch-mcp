# FastSearch MCP Bridge - Testing Guide

**Date:** November 15, 2025  
**Status:** Testing Suite Created

## Overview

This guide covers testing the FastSearch MCP bridge server, its integration with Claude Desktop, and all available tools.

## Test Scripts

### 1. Integration Test Suite

**File:** `test_mcp_bridge_integration.py`

**Purpose:** Comprehensive test of server initialization, tool registration, JSON-RPC communication, and Claude Desktop configuration.

**Usage:**
```powershell
python test_mcp_bridge_integration.py
```

**Tests:**
1. ✅ Server initialization
2. ✅ Tool registration (all 15 tools)
3. ✅ JSON-RPC communication structure
4. ✅ Tool execution
5. ✅ Claude Desktop configuration generation
6. ✅ C++ service connection

**Output:**
- Validates all components
- Generates Claude Desktop config file
- Reports test results

### 2. Interactive Tool Tester

**File:** `test_mcp_tools_interactive.py`

**Purpose:** Interactive testing of individual tools.

**Usage:**
```powershell
# Interactive mode
python test_mcp_tools_interactive.py

# Test specific tool
python test_mcp_tools_interactive.py service_status
python test_mcp_tools_interactive.py file_search pattern="*.txt" max_results=5
```

## Claude Desktop Configuration

### Automatic Configuration

The integration test automatically generates and writes the Claude Desktop configuration to:
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Manual Configuration

Add this to your Claude Desktop config:

```json
{
  "mcpServers": {
    "fastsearch": {
      "command": "python",
      "args": [
        "-m",
        "fastsearch_mcp"
      ],
      "cwd": "D:\\Dev\\repos\\fastsearch-mcp",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Note:** Adjust `cwd` to your project root path.

### Configuration Location

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

## Testing Workflow

### Step 1: Run Integration Tests

```powershell
cd d:\Dev\repos\fastsearch-mcp
python test_mcp_bridge_integration.py
```

**Expected Output:**
```
======================================================================
  Test 1: Server Initialization
======================================================================
✅ Server created successfully (version 0.5.0)
ℹ️  Server name: fastsearch-mcp
ℹ️  FastMCP app initialized: True

======================================================================
  Test 2: Tool Registration
======================================================================
ℹ️  Available tools from registry: 15
✅   - file_search: Search for files using direct NTFS MFT access...
✅   - service_status: Get the current status of the FastSearch service...
...
✅ All 15 tools registered successfully

======================================================================
  Test 3: JSON-RPC Communication
======================================================================
...
```

### Step 2: Test Individual Tools

```powershell
python test_mcp_tools_interactive.py
```

Select tools from the menu and test them interactively.

### Step 3: Verify Claude Desktop Integration

1. **Check config file was created:**
   ```powershell
   Get-Content "$env:APPDATA\Claude\claude_desktop_config.json" | ConvertFrom-Json | ConvertTo-Json -Depth 10
   ```

2. **Restart Claude Desktop** (required for config changes)

3. **Verify server starts:**
   - Open Claude Desktop
   - Check server logs (if available)
   - Try using a tool in Claude

### Step 4: Test Tools in Claude Desktop

**Example prompts to test in Claude:**

1. **Service Status:**
   ```
   Check the status of the FastSearch service
   ```

2. **File Search:**
   ```
   Search for all .txt files on my C: drive
   ```

3. **Disk Analysis:**
   ```
   Analyze disk usage on C: drive
   ```

## Available Tools

The MCP bridge provides 15 tools:

1. **file_search** - Direct NTFS MFT file search
2. **file_content_search** - Text pattern search in files
3. **disk_analyzer** - Disk usage analysis
4. **duplicate_finder** - Find duplicate files
5. **integrity_checker** - File integrity verification
6. **resource_monitor** - System resource monitoring
7. **service_status** - FastSearch service status
8. **list_services** - List Windows services
9. **get_service** - Get service details
10. **start_service** - Start a service
11. **stop_service** - Stop a service
12. **restart_service** - Restart a service
13. **set_service_startup_type** - Configure service startup
14. **get_service_logs** - Retrieve service logs
15. **help** - Tool documentation

## Troubleshooting

### Server Won't Start

**Check:**
1. Python path is correct in config
2. Module can be imported: `python -m fastsearch_mcp`
3. Dependencies installed: `pip install -r requirements.txt`

### Tools Not Available in Claude

**Check:**
1. Claude Desktop restarted after config change
2. Server is running (check Claude Desktop logs)
3. Config file syntax is valid JSON

### Service Connection Issues

**Check:**
1. C++ service is running: `Get-Service -Name FastSearchMCP`
2. Named pipe exists: `\\.\pipe\FastSearchMCP`
3. Service logs: `python tests/read_service_logs.py`

## Next Steps

After successful testing:

1. ✅ Verify all tools work in Claude Desktop
2. ✅ Test file search with direct MFT access
3. ✅ Benchmark performance
4. ✅ Document any issues found
5. ✅ Update status report

## Test Results

**Last Run:** November 15, 2025

**Status:** ✅ All integration tests passing

**Tools Registered:** 15/15

**Service Connection:** ✅ Working (direct MFT access enabled)

