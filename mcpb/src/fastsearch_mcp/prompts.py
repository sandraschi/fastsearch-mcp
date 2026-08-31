"""
FastMCP 3.2 prompt templates for FastSearch MCP.

Registered via @mcp.prompt() decorator at import time.
"""

from fastsearch_mcp.mcp_instance import mcp


@mcp.prompt()
def search_files_guide() -> str:
    """Guide: How to search files with FastSearch MCP."""
    return """# FastSearch MCP - File Search Guide

## Basic Usage
Use `fastsearch_search` with a glob pattern and path:
- `fastsearch_search(pattern="*.txt", path="C:\\")`
- `fastsearch_search(pattern="README.md", path="D:\\Projects")`

## Search All Drives
Set `search_all=True` to search every NTFS drive:
- `fastsearch_search(pattern="*.log", search_all=True, max_results=50)`

## Advanced Filtering
Use `fastsearch_search_advanced` for size, date, and attribute filters:
- Size: `min_size=1048576` (1MB+), `max_size=1073741824` (1GB-)
- Date: `modified_after="7d"`, `created_before="2024-01-01"`
- Attributes: `include_hidden=True`, `include_system=False`

## Content Search
Use `file_content_search` to find text inside files:
- `file_content_search(search_pattern="TODO", search_dir="C:\\Projects", file_pattern="*.py")`

## Service Management
- Check status: `service_status`
- Start/stop: `service_start_fastsearch`, `service_stop_fastsearch`
- The FastSearch Windows service must be running for all search operations
"""


@mcp.prompt()
def disk_analysis_guide() -> str:
    """Guide: How to analyze disk usage and find duplicates."""
    return """# FastSearch MCP - Disk Analysis Guide

## Drive Inventory
List all drives: `drive_inventory`

## Disk Usage Analysis
Analyze space usage: `analyze_disk_usage(path="C:\\", max_depth=3)`
- Shows top-level folder sizes
- Use `max_depth` to control drill-down depth
- Use `min_size_mb` to filter out small folders

## Find Duplicate Files
Detect duplicates by content hash: `find_duplicate_files(directories=["C:\\Users"], pattern="*.jpg", min_size=102400)`
- Filters by pattern and minimum size
- Returns groups of identical files with paths and sizes

## File Integrity
Generate file hashes: `generate_file_hashes(paths=["C:\\important"], algorithm="sha256")`
- Supports sha256, sha512, md5, blake2b
- Verify integrity by re-running and comparing hashes

## System Resources
- Current resource usage: `monitor_system_resources(duration_seconds=5)`
- Process information: `get_process_info()`
"""


@mcp.prompt()
def service_troubleshooting() -> str:
    """Guide: Troubleshoot FastSearch service issues."""
    return """# FastSearch MCP - Service Troubleshooting

## Service Not Running
If searches return "service not available":
1. Check status: `service_status`
2. Start the service: `service_start_fastsearch` (requires admin)
3. The service must be installed first via the MSI installer

## Named Pipe Connection Issues
Error: "All pipe instances are busy" or "File not found"
- The service binary path: `D:\\Dev\\repos\\fastsearch-mcp\\service\\build\\bin\\Release\\FastSearchServiceNew.exe`
- Verify the service is running in Windows Services (services.msc)
- Restart: `service_restart_fastsearch`
- Check Windows Event Log for FastSearch errors

## Zero Search Results
If `fastsearch_search` returns 0 results:
- The C++ service's MFT record parsing may have a struct alignment issue
- Rebuild the service from source and restart
- Verify the named pipe connection with `service_status`
"""
