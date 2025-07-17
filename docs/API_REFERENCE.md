# FastSearch MCP - API Reference

**Project**: FastSearch MCP Server  
**Version**: 1.0  
**Date**: July 17, 2025  
**Protocol**: Model Context Protocol (MCP) + HTTP REST API  

## 🔌 **MCP Tools Interface**

### **Protocol Overview**

FastSearch MCP implements the Model Context Protocol for seamless Claude Desktop integration. All communication uses JSON-RPC 2.0 over stdin/stdout.

**Base Message Format**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      // Tool-specific parameters
    }
  }
}
```

**Response Format**:
```json
{
  "jsonrpc": "2.0", 
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Tool execution results"
      }
    ]
  }
}
```

### **Tool 1: fast_search**

**Description**: Lightning-fast file search using direct NTFS Master File Table access

#### **Input Schema**
```json
{
  "name": "fast_search",
  "description": "Search for files using patterns with sub-100ms performance",
  "inputSchema": {
    "type": "object",
    "properties": {
      "pattern": {
        "type": "string",
        "description": "File pattern to search for. Supports wildcards: *.js, config.*, README, etc.",
        "examples": ["*.py", "config.*", "package.json", "*.exe"]
      },
      "path": {
        "type": "string",
        "description": "Optional path filter to narrow search scope",
        "examples": ["src", "components", "node_modules"]
      },
      "drive": {
        "type": "string", 
        "description": "Drive letter to search (C, D, E, etc.)",
        "default": "C"
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of results to return",
        "default": 1000,
        "minimum": 1,
        "maximum": 10000
      },
      "min_size_bytes": {
        "type": "integer",
        "description": "Minimum file size in bytes (optional filter)",
        "minimum": 0
      },
      "max_size_bytes": {
        "type": "integer", 
        "description": "Maximum file size in bytes (optional filter)",
        "minimum": 0
      },
      "include_hidden": {
        "type": "boolean",
        "description": "Include hidden files in results",
        "default": false
      },
      "case_sensitive": {
        "type": "boolean",
        "description": "Case-sensitive pattern matching",
        "default": false
      }
    },
    "required": ["pattern"]
  }
}
```

#### **Example Requests**

**Basic File Search**:
```json
{
  "name": "fast_search",
  "arguments": {
    "pattern": "*.js",
    "path": "src",
    "max_results": 100
  }
}
```

**Configuration File Search**:
```json
{
  "name": "fast_search", 
  "arguments": {
    "pattern": "config.*",
    "drive": "D",
    "include_hidden": true
  }
}
```

**Large File Search**:
```json
{
  "name": "fast_search",
  "arguments": {
    "pattern": "*",
    "min_size_bytes": 104857600,
    "max_results": 50
  }
}
```

#### **Response Format**
```json
{
  "results": [
    {
      "path": "C:\\Users\\user\\Documents\\project\\src\\main.js",
      "name": "main.js",
      "size": 15420,
      "size_human": "15.1 KB",
      "modified": "2025-07-17T10:30:45Z",
      "created": "2025-07-15T14:22:10Z",
      "extension": "js",
      "is_directory": false,
      "is_hidden": false,
      "attributes": ["archive"]
    }
  ],
  "search_stats": {
    "total_found": 156,
    "returned": 100,
    "search_time_ms": 45,
    "files_scanned": 1234567,
    "pattern": "*.js",
    "drive": "C"
  }
}
```

### **Tool 2: find_large_files**

**Description**: Discover the largest files on your system for storage analysis

#### **Input Schema**
```json
{
  "name": "find_large_files",
  "description": "Find the largest files on the system, sorted by size",
  "inputSchema": {
    "type": "object",
    "properties": {
      "min_size_mb": {
        "type": "integer",
        "description": "Minimum file size in megabytes",
        "default": 100,
        "minimum": 1
      },
      "drive": {
        "type": "string",
        "description": "Drive letter to scan (C, D, E, etc.)",
        "default": "C"
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of results to return",
        "default": 50,
        "minimum": 1,
        "maximum": 1000
      },
      "file_types": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Optional file extensions to filter by",
        "examples": [["mp4", "avi", "mkv"], ["zip", "rar", "7z"]]
      },
      "exclude_system": {
        "type": "boolean",
        "description": "Exclude Windows system directories",
        "default": true
      }
    }
  }
}
```

#### **Example Requests**

**Find Large Video Files**:
```json
{
  "name": "find_large_files",
  "arguments": {
    "min_size_mb": 500,
    "file_types": ["mp4", "avi", "mkv", "mov"],
    "max_results": 20
  }
}
```

**Storage Cleanup Analysis**:
```json
{
  "name": "find_large_files",
  "arguments": {
    "min_size_mb": 50,
    "exclude_system": true,
    "max_results": 100
  }
}
```

#### **Response Format**
```json
{
  "results": [
    {
      "path": "C:\\Users\\user\\Videos\\movie.mp4",
      "name": "movie.mp4", 
      "size": 2147483648,
      "size_human": "2.0 GB",
      "modified": "2025-07-10T16:45:30Z",
      "extension": "mp4",
      "size_rank": 1
    }
  ],
  "summary": {
    "total_files_found": 45,
    "total_size_bytes": 52428800000,
    "total_size_human": "48.8 GB",
    "largest_file_size": 2147483648,
    "average_file_size": 1165084444,
    "scan_time_ms": 234
  }
}
```

### **Tool 3: benchmark_search**

**Description**: Performance testing and system capability analysis

#### **Input Schema**
```json
{
  "name": "benchmark_search",
  "description": "Run comprehensive search performance benchmarks",
  "inputSchema": {
    "type": "object",
    "properties": {
      "drive": {
        "type": "string",
        "description": "Drive letter to benchmark (C, D, E, etc.)",
        "default": "C"
      },
      "test_patterns": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Custom patterns to test",
        "default": ["*.exe", "*.dll", "*.js", "*.txt", "config.*"]
      },
      "iterations": {
        "type": "integer",
        "description": "Number of test iterations per pattern",
        "default": 3,
        "minimum": 1,
        "maximum": 10
      },
      "include_system_info": {
        "type": "boolean",
        "description": "Include system hardware information",
        "default": true
      }
    }
  }
}
```

#### **Example Request**
```json
{
  "name": "benchmark_search",
  "arguments": {
    "drive": "C",
    "test_patterns": ["*.js", "*.py", "*.exe"],
    "iterations": 5
  }
}
```

#### **Response Format**
```json
{
  "benchmark_results": [
    {
      "pattern": "*.js",
      "iterations": 5,
      "avg_time_ms": 42.3,
      "min_time_ms": 38.1,
      "max_time_ms": 47.8,
      "files_found": 15420,
      "throughput_files_per_ms": 364.3
    }
  ],
  "system_info": {
    "drive_type": "SSD",
    "drive_size_gb": 512,
    "drive_free_gb": 128,
    "total_files_estimated": 1234567,
    "os_version": "Windows 11",
    "cpu_cores": 8,
    "memory_gb": 16
  },
  "performance_grade": "A+",
  "recommendations": [
    "Performance is excellent for this drive size",
    "Consider increasing max_results for better throughput"
  ]
}
```

## 🌐 **HTTP REST API** (Optional)

### **Base Configuration**

**Default Endpoint**: `http://localhost:3000`  
**Content-Type**: `application/json`  
**CORS**: Enabled for frontend integration  

### **Authentication**

**Development Mode**: No authentication required  
**Production Mode**: API key via `X-API-Key` header (if configured)  

### **Endpoints**

#### **GET /health**
**Description**: Health check and server status

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "ntfs_access": true,
  "drives_available": ["C", "D"]
}
```

#### **POST /search**
**Description**: File search endpoint

**Request Body**:
```json
{
  "pattern": "*.js",
  "path": "src",
  "max_results": 100
}
```

**Response**: Same as MCP `fast_search` tool

#### **POST /large-files**
**Description**: Large file discovery

**Request Body**:
```json
{
  "min_size_mb": 100,
  "max_results": 50
}
```

**Response**: Same as MCP `find_large_files` tool

#### **POST /benchmark**
**Description**: Performance benchmarking

**Request Body**:
```json
{
  "drive": "C",
  "iterations": 3
}
```

**Response**: Same as MCP `benchmark_search` tool

#### **GET /stats**
**Description**: Server statistics and metrics

**Response**:
```json
{
  "total_searches": 1042,
  "total_files_found": 156789,
  "average_search_time_ms": 67.3,
  "cache_hit_rate": 0.0,
  "memory_usage_mb": 23.4,
  "uptime_hours": 24.5
}
```

## 🔧 **Error Handling**

### **Common Error Codes**

| Code | Description | Resolution |
|------|-------------|------------|
| **1001** | Invalid pattern syntax | Check glob pattern format |
| **1002** | Drive not accessible | Verify drive exists and permissions |
| **1003** | NTFS access denied | Run as Administrator |
| **1004** | Path not found | Check path parameter |
| **1005** | Size limits invalid | Check min/max size parameters |
| **1006** | Too many results | Reduce max_results or narrow pattern |

### **Error Response Format**

**MCP Error**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": 1003,
    "message": "NTFS access denied - Administrator privileges required",
    "data": {
      "drive": "C",
      "resolution": "Run as Administrator or grant SeBackupPrivilege"
    }
  }
}
```

**HTTP Error**:
```json
{
  "error": {
    "code": 1003,
    "message": "NTFS access denied - Administrator privileges required",
    "details": {
      "drive": "C",
      "resolution": "Run as Administrator or grant SeBackupPrivilege"
    }
  },
  "request_id": "req_123456789"
}
```

## 📊 **Rate Limiting & Performance**

### **Built-in Limits**

| Parameter | Default | Maximum | Purpose |
|-----------|---------|---------|---------|
| **max_results** | 1000 | 10000 | Prevent memory overflow |
| **concurrent_searches** | 5 | 10 | Limit system load |
| **search_timeout_ms** | 10000 | 30000 | Prevent hanging |
| **pattern_complexity** | 50 chars | 200 chars | Prevent ReDoS |

### **Performance Guidelines**

**Optimal Performance**:
- Use specific patterns when possible (`package.json` vs `*`)
- Include path filters to narrow scope
- Set reasonable max_results (100-1000)
- Avoid overly complex regex patterns

**Memory Considerations**:
- Each result consumes ~200 bytes
- 10,000 results ≈ 2MB memory
- Keep max_results under 5,000 for best performance

## 🔍 **Usage Examples**

### **Common Search Patterns**

**Find all JavaScript files**:
```json
{"pattern": "*.js"}
```

**Find configuration files**:
```json
{"pattern": "config.*"}
```

**Find README files**:
```json
{"pattern": "README*"}
```

**Find specific file**:
```json
{"pattern": "package.json"}
```

**Find in specific directory**:
```json
{"pattern": "*.py", "path": "src"}
```

**Find large executables**:
```json
{"pattern": "*.exe", "min_size_bytes": 10485760}
```

### **Performance Optimization Examples**

**Fast specific search**:
```json
{
  "pattern": "webpack.config.js",
  "path": "projects",
  "max_results": 10
}
```

**Efficient large file discovery**:
```json
{
  "min_size_mb": 100,
  "max_results": 20,
  "exclude_system": true
}
```

**Targeted benchmark**:
```json
{
  "test_patterns": ["*.js"],
  "iterations": 1,
  "include_system_info": false
}
```

## 🛠️ **Development & Debugging**

### **Debug Mode**

**Enable verbose logging**:
```bash
RUST_LOG=debug fastsearch.exe --mcp-server
```

**Enable trace logging**:
```bash
RUST_LOG=trace fastsearch.exe --mcp-server  
```

### **Manual Testing**

**Test MCP Protocol**:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | fastsearch.exe --mcp-server
```

**Test HTTP API**:
```bash
curl -X POST http://localhost:3000/search \
  -H "Content-Type: application/json" \
  -d '{"pattern":"*.js","max_results":10}'
```

### **Configuration Files**

**MCP Server Config** (`~/.config/fastsearch/config.json`):
```json
{
  "max_concurrent_searches": 5,
  "default_max_results": 1000,
  "enable_http_api": true,
  "http_port": 3000,
  "log_level": "info"
}
```

---

## 🚀 **Quick Reference Card**

### **Most Common Usage**
```json
// Basic file search
{"tool": "fast_search", "pattern": "*.js"}

// Find large files
{"tool": "find_large_files", "min_size_mb": 100}

// Performance test
{"tool": "benchmark_search", "drive": "C"}
```

### **Key Performance Tips**
1. **Use specific patterns** - `package.json` vs `*`
2. **Add path filters** - `"path": "src"` to narrow scope  
3. **Set reasonable limits** - `max_results: 100-1000`
4. **Exclude system files** - for storage analysis

### **Troubleshooting Checklist**
- ✅ Run as Administrator for NTFS access
- ✅ Check drive exists and is accessible
- ✅ Verify pattern syntax (glob format)
- ✅ Monitor memory usage with large result sets
- ✅ Check logs with `RUST_LOG=debug`

**FastSearch MCP: Professional file search at your fingertips** 🚀