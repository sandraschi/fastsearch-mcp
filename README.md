# FastSearch MCP Server

Lightning-fast file search for Claude Desktop using NTFS Master File Table with privilege separation architecture.

## Architecture

**Bridge + Service Architecture**: Secure privilege separation for seamless Claude integration.

### Components

1. **FastSearch Bridge** (`bridge/`) - **User-mode MCP server**
   - Runs at user privilege level (no UAC during normal operation)
   - Handles MCP protocol communication with Claude Desktop
   - Validates requests and forwards to elevated service
   - **This is what Claude Desktop calls**

2. **FastSearch Service** (`service/`) - **Elevated NTFS engine**
   - Windows service with elevated privileges for NTFS MFT access
   - Performs actual file searches with direct Master File Table reading
   - Serves requests via named pipes
   - Installed once with admin rights, runs automatically

3. **Shared Types** (`shared/`) - **Common data structures**
   - Request/response types shared between bridge and service
   - Serialization for IPC communication

## Directory Structure

```
fastsearch-mcp/
├── bridge/                    # MCP Bridge (user-mode)
│   ├── src/
│   │   ├── main.rs           # MCP server entry point
│   │   ├── mcp_bridge.rs     # MCP protocol handler
│   │   ├── ipc_client.rs     # Named pipe client
│   │   ├── validation.rs     # Request validation
│   │   └── lib.rs
│   ├── Cargo.toml
│   └── target/release/
│       └── fastsearch-mcp-bridge.exe  ✅ CLAUDE DESKTOP CALLS THIS
├── service/                   # FastSearch Service (elevated)
│   ├── src/
│   │   ├── main.rs           # Service entry point
│   │   ├── search_engine.rs  # Search logic (was mcp_server.rs)
│   │   ├── ntfs_reader.rs    # NTFS MFT reader
│   │   ├── web_api.rs        # Web API for frontend
│   │   └── lib.rs
│   └── Cargo.toml
├── shared/                    # Common types
│   ├── src/
│   │   ├── types.rs          # SearchRequest, SearchResponse, etc.
│   │   └── lib.rs
│   └── Cargo.toml
├── installer/                 # One-time UAC installation
├── frontend/                  # Web UI
└── Cargo.toml                # Workspace root
```

## Installation & Usage

### One-Time Installation (UAC Required)
```bash
# Download installer from GitHub releases
# Run installer as Administrator (one-time UAC prompt)
setup.exe
```

**What the installer does:**
- Installs FastSearch service with elevated privileges
- Installs MCP bridge for Claude Desktop
- Registers service for automatic startup
- Sets up named pipe communication

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fastsearch": {
      "command": "D:\\Dev\\repos\\fastsearch-mcp\\bridge\\target\\release\\fastsearch-mcp-bridge.exe"
    }
  }
}
```

### Normal Operation (No UAC)
- **Service runs automatically** - No user intervention needed
- **Bridge connects to Claude** - User-level operation only
- **Fast NTFS searches** - Sub-100ms response times
- **Seamless integration** - No privilege prompts during use

## Development

### Build All Components
```bash
cargo build --release
```

### Build Individual Components
```bash
# Build bridge only
cd bridge && cargo build --release

# Build service only  
cd service && cargo build --release

# Build shared types
cd shared && cargo build --release
```

### Test Architecture
```bash
# Test bridge standalone
./bridge/target/release/fastsearch-mcp-bridge.exe

# Test service (requires admin)
./service/target/release/fastsearch-service.exe
```

## Why This Architecture?

### Problem
- **NTFS MFT access requires elevated privileges**
- **Claude Desktop cannot run elevated MCP servers**
- **Users don't want UAC prompts during normal operation**

### Solution  
- **Service**: Runs elevated, handles NTFS access, installed once
- **Bridge**: Runs as user, handles MCP protocol, no elevation needed
- **Communication**: Named pipes for secure IPC

### Benefits
- ✅ **No UAC during normal use** - Only during installation
- ✅ **Secure privilege separation** - Service isolated from MCP protocol
- ✅ **Fast performance** - Direct NTFS MFT access
- ✅ **Seamless Claude integration** - Standard MCP server interface
- ✅ **Robust error handling** - Graceful degradation if service unavailable

## Features

- **Lightning-fast search** - Direct NTFS Master File Table reading
- **Multiple search types** - Exact, glob, regex, fuzzy matching
- **Real-time results** - Sub-100ms response times
- **Privilege separation** - Secure bridge/service architecture
- **Graceful fallback** - Helpful messages if service unavailable
- **Web interface** - Optional frontend for direct access

## License

MIT - Sandra & Claudius
