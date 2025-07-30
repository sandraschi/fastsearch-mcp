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

### Prerequisites
- Windows 10/11 with NTFS file system
- Rust toolchain (for building from source)
- Administrator privileges (required for initial setup only)

### Manual Installation (Recommended for Development)

1. **Build the project** (from an elevated command prompt):
   ```powershell
   # Clone the repository
   git clone https://github.com/yourusername/fastsearch-mcp.git
   cd fastsearch-mcp
   
   # Build in release mode
   cargo build --release
   ```

2. **Install the Windows Service** (one-time setup with admin rights):
   ```powershell
   # Run as Administrator
   $servicePath = "D:\Dev\repos\fastsearch-mcp\target\release\fastsearch.exe"
   sc.exe create FastSearch binPath= "$servicePath --run-as-service" start= auto
   sc.exe description FastSearch "FastSearch MCP Service for lightning-fast file search using NTFS MFT"
   sc.exe start FastSearch
   ```
   
   > **Note**: Update `$servicePath` to match your actual path to the built `fastsearch.exe`

3. **Verify the service is running**:
   ```powershell
   sc.exe query FastSearch
   ```

### One-Click Installer (Coming Soon)
```powershell
# Download installer from GitHub releases
# Run installer as Administrator (one-time UAC prompt)
setup.exe
```

**What the installer will do:**
- Install FastSearch service with elevated privileges
- Register service for automatic startup
- Set up named pipe communication
- Configure the MCP bridge for Claude Desktop

### Claude Desktop Configuration

Add to your Claude Desktop configuration (typically in `settings.json` or via UI):

```json
{
  "mcpServers": {
    "fastsearch": {
      "command": "D:\\Dev\\repos\\fastsearch-mcp\\target\\release\\fastsearch-mcp-bridge.exe",
      "args": ["--service-pipe", "\\\\\\.\\pipe\\fastsearch-service"],
      "timeout": 30,
      "autoStart": true,
      "enabled": true,
      "description": "FastSearch MCP Bridge for lightning-fast file search using NTFS MFT"
    }
  }
}
```

> **Note**: Update the path to point to your `fastsearch-mcp-bridge.exe` location

### Normal Operation (Privilege Separation)

- **Service (Elevated)**
  - Runs automatically at system startup
  - Has direct NTFS MFT access
  - Listens on named pipe: `\\.\pipe\fastsearch-service`
  - No UI, runs in background

- **Bridge (User Mode)**
  - Started by Claude Desktop
  - Runs with normal user privileges
  - Forwards requests to elevated service
  - No UAC prompts during normal use

- **Performance**
  - Sub-100ms search response times
  - Minimal memory footprint
  - Efficient NTFS MFT scanning

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
- **REST API** - Web interface for integration with other applications

## Documentation

- [Project Plan](projects/FastSearch%20MCP%20Server%20-%20Project%20Plan.md)
- [MCP Ecosystem](MCP_ECOSYSTEM.md) - About MCP protocol and ecosystem
- [Web API](WEB_API.md) - REST API documentation for web and application integration

## Release Process

FastSearch MCP uses GitHub Actions for automated builds and releases. The release process is fully automated:

1. Create a version tag (e.g., `v1.0.0`)
2. Push the tag to trigger the release workflow
3. GitHub Actions builds for all platforms
4. Artifacts are uploaded to GitHub Releases

For detailed release instructions, see [RELEASING.md](RELEASING.md).

### Testing a Release Locally

Before creating a release, test the build process locally:

```powershell
# Run the test script
.\test-release.ps1
```

This will verify that all components build correctly and the installer is created successfully.
- **Web interface** - Optional frontend for direct access

## License

MIT - Sandra & Claudius
