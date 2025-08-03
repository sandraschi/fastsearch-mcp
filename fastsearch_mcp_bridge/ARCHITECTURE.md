# FastSearch MCP Bridge - Architecture and Implementation

## System Overview

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  Claude Desktop  |<--->|  FastSearch MCP  |<--->|  FastSearch     |
|  (MCP Client)    |     |  Bridge          |     |  Windows Service |
|                  |     |  (User Mode)     |     |  (Elevated)      |
+------------------+     +------------------+     +------------------+
```

## Component Breakdown

### 1. FastSearch Windows Service (Elevated)
- **Privilege Level**: SYSTEM/Administrator
- **Responsibilities**:
  - Direct NTFS MFT (Master File Table) access
  - High-performance file system indexing and searching
  - Secure IPC endpoint for bridge communication
- **Communication**:
  - Named Pipe: `\\.\pipe\fastsearch-service`
  - Binary protocol over pipes
  - Authentication and message signing

### 2. FastSearch MCP Bridge (User Mode)
- **Privilege Level**: Standard User
- **Responsibilities**:
  - FastMCP 2.10 compliant JSON-RPC server
  - Protocol translation (MCP <-> FastSearch)
  - Request validation and sanitization
  - Rate limiting and access control
- **Communication**:
  - STDIN/STDOUT for MCP protocol
  - Named Pipe for service communication

### 3. Claude Desktop Integration
- **MCP Protocol**:
  - JSON-RPC 2.0 over STDIO
  - Full FastMCP 2.10 feature set
  - Asynchronous request/response
  - Streaming results support

## Implementation Details

### MCP Bridge (Python)

#### Core Components
1. **MCP Server**
   - `McpServer` class implementing FastMCP 2.10
   - Async I/O for high concurrency
   - Proper error handling and recovery

2. **Service Client**
   - `FastSearchClient` for IPC communication
   - Connection pooling and retry logic
   - Message serialization/deserialization

3. **Protocol Adapters**
   - MCP to FastSearch request translation
   - Response formatting and normalization
   - Error code mapping

#### Dependencies
- Python 3.8+
- `pywin32` (Windows named pipes)
- `pydantic` (Data validation)
- `python-jsonrpc-server` (MCP protocol)
- `python-dotenv` (Configuration)

### Windows Service (Existing)
- C++/Rust implementation
- NTFS MFT access
- Performance-optimized search algorithms
- Secure IPC endpoint

## DXT Packaging

### Package Structure
```
fastsearch-mcp.dxt/
├── bin/
│   └── fastsearch-mcp-bridge.exe  # PyInstaller bundle
├── prompts/
│   └── search.md                  # Main prompt template
├── config.json                    # DXT configuration
└── README.md                      # User documentation
```

### Configuration
```json
{
  "name": "fastsearch-mcp",
  "version": "1.0.0",
  "description": "FastSearch MCP Bridge for Claude Desktop",
  "entrypoint": "bin/fastsearch-mcp-bridge.exe",
  "capabilities": ["filesystem_search"],
  "permissions": {
    "filesystem": {
      "read": ["*"],
      "watch": ["*"]
    }
  }
}
```

## Security Considerations

1. **Privilege Separation**
   - Service runs with minimal required privileges
   - Bridge runs as unprivileged user
   - Secure IPC with message authentication

2. **Input Validation**
   - Strict schema validation
   - Path sanitization
   - Query parameter validation

3. **Rate Limiting**
   - Request throttling
   - Result size limits
   - Timeout handling

## Testing Strategy

### Unit Tests
- MCP protocol compliance
- Request/response handling
- Error conditions

### Integration Tests
- End-to-end with mock service
- Named pipe communication
- Error recovery

### Performance Testing
- Search latency
- Concurrent request handling
- Memory usage

## Deployment

### Prerequisites
1. FastSearch Windows Service installed
2. Python 3.8+ runtime
3. DXT-compatible Claude Desktop

### Installation
1. Install FastSearch Windows Service (elevated)
2. Install DXT package in Claude Desktop
3. Configure service pipe path if non-default

## Monitoring and Logging

### Logging
- Structured JSON logging
- Configurable log levels
- Rotation and retention

### Metrics
- Request rates
- Search performance
- Error rates
- Resource usage

## Future Enhancements

1. **Advanced Search**
   - Content-based search
   - Metadata filtering
   - Saved searches

2. **Performance**
   - Result caching
   - Query optimization
   - Index management

3. **Security**
   - TLS for IPC
   - Audit logging
   - Access control lists

## Compliance

- FastMCP 2.10 Specification
- Windows Security Best Practices
- Performance and Reliability Standards
