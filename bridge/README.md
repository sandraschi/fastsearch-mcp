# FastSearch MCP Bridge

Lightning-fast file search bridge for Claude Desktop using NTFS Master File Table access.

## 🚀 Quick Start

```bash
# Build the bridge
cargo build --release

# The binary will be at: target/release/fastsearch-mcp-bridge.exe
```

## 📋 Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fastsearch": {
      "command": "C:\\path\\to\\fastsearch-mcp-bridge.exe"
    }
  }
}
```

## 🛠️ Development

```bash
# Run in development mode
cargo run

# Run tests
cargo test

# Check linting
cargo clippy
```

## 🔧 Architecture

This bridge provides a user-mode MCP interface to the FastSearch admin service:

- **MCP Protocol**: JSON-RPC 2.0 over stdin/stdout
- **Service Communication**: Named pipes to admin service
- **Security**: Input validation and privilege separation
- **Fallback**: Helpful guidance when service unavailable

## 📦 Tools Available

- `fast_search` - Lightning-fast file search (sub-100ms)
- `search_stats` - Performance metrics and service status
- `service_status` - Installation help and status check

## 🛡️ Security

- Path traversal protection
- Input validation on all parameters
- No elevation required (bridge runs as user)
- Admin service handles privileged operations

## 📄 License

MIT License - see LICENSE file for details.
