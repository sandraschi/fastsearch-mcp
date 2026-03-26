# Claude Desktop Testing Guide

**Date:** November 15, 2025  
**Status:** Ready for Testing

## ✅ Configuration Complete

The FastSearch MCP server has been added to your Claude Desktop configuration:

**Location:** `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "fastsearch": {
      "command": "python",
      "args": ["-m", "fastsearch_mcp"],
      "cwd": "D:\\Dev\\repos\\fastsearch-mcp",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## 🚀 Testing Steps

### Step 1: Restart Claude Desktop

**IMPORTANT:** Claude Desktop must be restarted for configuration changes to take effect.

1. Close Claude Desktop completely
2. Reopen Claude Desktop
3. Wait for MCP servers to initialize

### Step 2: Verify Server Connection

**In Claude Desktop, try:**
```
Check if the FastSearch MCP server is connected
```

**Or:**
```
What MCP servers are available?
```

**Expected:** FastSearch MCP should appear in the list of available servers.

### Step 3: Test Service Status

**In Claude Desktop, try:**
```
Check the status of the FastSearch service
```

**Expected Response:**
- Service status (running/stopped)
- Service executable path
- Named pipe connection status
- Direct MFT access status

### Step 4: Test File Search (Direct MFT Access!)

**In Claude Desktop, try:**
```
Search for all .txt files on my C: drive using FastSearch
```

**Or:**
```
Find all Python files (*.py) in my D:\Dev directory
```

**Expected:**
- Fast results (<1 second for typical searches)
- Results from direct MFT access
- File paths, sizes, and modification times

### Step 5: Test Other Tools

**Disk Analysis:**
```
Analyze disk usage on my C: drive
```

**Service Management:**
```
List all Windows services
```

**Resource Monitoring:**
```
Monitor system resources
```

## 📊 Available Tools in Claude Desktop

1. **file_content_search** - Search for text in files
2. **analyze_disk_usage** - Disk usage analysis
3. **find_duplicate_files** - Find duplicate files
4. **check_file_integrity** - File integrity checks
5. **monitor_system_resources** - System monitoring
6. **service_status** - FastSearch service status
7. **list_services** - List Windows services
8. **get_service** - Get service details
9. **start_service** - Start a service
10. **stop_service** - Stop a service
11. **restart_service** - Restart a service
12. **set_service_startup_type** - Configure startup
13. **get_service_logs** - Retrieve service logs
14. **help** - Tool documentation

## 🔍 Verification Checklist

- [ ] Claude Desktop restarted
- [ ] FastSearch MCP appears in server list
- [ ] `service_status` tool works
- [ ] File search returns results
- [ ] Results come from direct MFT access (check logs)
- [ ] Other tools work as expected

## 🐛 Troubleshooting

### Server Not Appearing

**Check:**
1. Config file syntax is valid JSON
2. Python path is correct
3. Module can be imported: `python -m fastsearch_mcp`
4. Claude Desktop was restarted

### Tools Not Working

**Check:**
1. C++ service is running: `Get-Service -Name FastSearchMCP`
2. Service logs: `python tests/read_service_logs.py`
3. Claude Desktop logs for errors

### File Search Slow

**Check:**
1. Service is using direct MFT access (check logs)
2. Service is running: `Get-Service -Name FastSearchMCP`
3. Named pipe connection: `\\.\pipe\FastSearchMCP`

## 📝 Test Results Template

**Date:** _______________

**Claude Desktop Version:** _______________

**Tests:**
- [ ] Server appears in Claude Desktop
- [ ] `service_status` works
- [ ] File search works
- [ ] Direct MFT access confirmed (check logs)
- [ ] Performance acceptable (<1s for typical searches)

**Issues Found:**
- 

**Notes:**
- 

## 🎯 Success Criteria

✅ **Server connects to Claude Desktop**  
✅ **All 14 tools are available**  
✅ **File search uses direct MFT access**  
✅ **Search performance is sub-second**  
✅ **Service status reports correctly**  
✅ **No errors in Claude Desktop logs**

---

**Ready to test! Restart Claude Desktop and start using the tools!**

