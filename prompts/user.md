# FastSearch MCP User Guide

## Quick Start

FastSearch MCP provides lightning-fast file search on Windows using direct NTFS Master File Table access.

### Basic Search

Search for files using patterns:

```
Search for Python files: *.py
Find configuration files: *.config, *.json
Locate log files: *.log
```

### Advanced Search

Use different search types:

- **Glob patterns**: `*.py`, `test_*.txt`, `**/node_modules/**`
- **Regex**: `^test.*\.py$`, `\d{4}-\d{2}-\d{2}`
- **Exact match**: `package.json`
- **Fuzzy search**: `pkgjson` (finds `package.json`)

### Search Options

- **Include patterns**: Only search specific file types
- **Exclude patterns**: Skip directories like `node_modules`, `.git`
- **Case sensitive**: Match exact case
- **Path restriction**: Limit search to specific directories
- **Result limit**: Control maximum results (default: 100)

## Common Use Cases

### Find All Python Files

```
Tool: fastsearch.search
Query: *.py
Path: C:\Users\YourName\Projects
```

### Search for Large Files

```
Tool: disk_analyzer
Path: C:\
Depth: 2
```

### Find Duplicate Files

```
Tool: duplicate_finder
Path: C:\Users\YourName\Documents
Min Size: 1048576 (1MB)
```

### Search File Contents

```
Tool: file_content_search
Search Pattern: import fastmcp
File Pattern: *.py
Search Dir: C:\Projects
```

### Check Service Status

```
Tool: getStatus
Level: basic
```

## Service Management

### Start FastSearch Service

If searches fail, the service may not be running:

```
Tool: start_service
Service Name: FastSearchMCP
```

### View Service Logs

Troubleshoot issues by checking logs:

```
Tool: get_service_logs
Service Name: FastSearchMCP
Limit: 50
```

## Tips for Best Performance

1. **Use specific patterns**: `*.py` is faster than `*`
2. **Limit search scope**: Use path parameter to narrow search
3. **Exclude large directories**: Skip `node_modules`, `.git`, `venv`
4. **Set reasonable limits**: Start with 100 results, increase if needed
5. **Use glob for simple searches**: Regex is slower but more powerful

## Troubleshooting

### Service Not Available

If you see "service not available":
1. Check service status: `getStatus`
2. Start the service: `start_service` (requires elevation)
3. Use fallback: `fastsearch.search_basic`

### Access Denied

Some operations require administrator privileges:
- Starting/stopping services
- Accessing certain system directories
- Service management operations

### Slow Searches

- Narrow the search path
- Use more specific patterns
- Exclude large directories
- Reduce result limit
- Check if service is running (direct MFT access is much faster)

## Examples

### Find Configuration Files

```
fastsearch.search(
  query="*.config",
  path="C:\\Projects",
  exclude=["node_modules", ".git"]
)
```

### Search Recent Logs

```
file_content_search(
  search_pattern="ERROR",
  file_pattern="*.log",
  search_dir="C:\\Logs",
  modified_after="7d"
)
```

### Analyze Disk Usage

```
disk_analyzer(
  path="C:\\Users",
  depth=3
)
```

