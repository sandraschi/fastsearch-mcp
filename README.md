# FastSearch MCP Server

Lightning-fast file search using NTFS Master File Table access. Built for use with MCP clients like Claude, Windsurf, Cline, and other AI development tools.

## 🚀 Features

- **Direct NTFS MFT Access**: Reads Master File Table directly for instant results
- **Background Indexing**: Non-blocking file indexing with thread safety
- **Pattern Matching**: Supports wildcards (*.js, README*, etc.) and filters
- **MCP Protocol**: Full JSON-RPC implementation for MCP clients
- **Graceful Fallbacks**: Falls back to filesystem walk if MFT access fails
- **Real-time Status**: Index monitoring and manual reindexing controls

## 🎯 Why FastSearch?

Current file search tools are painfully slow for AI development workflows:
- Windows Explorer search: Terrible performance
- Basic filesystem MCPs: 30+ seconds for large directories  
- Node.js solutions: Memory inefficient, poor performance

FastSearch reads the NTFS Master File Table directly using the proven `ntfs-reader` crate.

## 🔧 Architecture

### Core Components
- **NTFS Reader**: Direct MFT access using `ntfs-reader` crate
- **MCP Server**: Full JSON-RPC protocol implementation
- **Background Indexer**: Thread-safe concurrent file indexing
- **Search Engine**: Pattern matching with filters and performance reporting

### MCP Tools
- `fast_search` - Pattern-based file search with filters
- `find_duplicates` - Content-based duplicate detection (planned)
- `index_status` - Indexing progress and statistics
- `reindex_drive` - Manual drive reindexing

## 📦 Installation

### Prerequisites
- **Windows** (NTFS filesystem required)
- **Administrator privileges** (for MFT access)
- **Rust toolchain** (for building from source)

### Build from Source
```bash
git clone <repository-url>
cd fastsearch-mcp
cargo build --release
```

## ⚙️ MCP Client Configuration

### Claude Desktop
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fastsearch": {
      "command": "D:/Dev/repos/fastsearch-mcp/target/release/fastsearch.exe",
      "args": ["--mcp-server"]
    }
  }
}
```

### Other MCP Clients
- **Windsurf**: Configure in MCP settings panel
- **Cline**: Add to MCP server configuration
- **Continue**: Include in MCP tools setup
- **Cursor**: Configure for MCP protocol support
- **Open Interpreter**: Add via MCP integration

## 🔧 Usage

### Command Line
```bash
# Run as MCP server (for any MCP client)
fastsearch --mcp-server

# Run performance benchmark
fastsearch --benchmark --drive C

# Show help
fastsearch --help
```

### From MCP Clients
```
Find all TypeScript files in my project
→ Uses fast_search tool with pattern "*.ts"

Show me large files modified today
→ Combines pattern matching with size/date filters

Check indexing status
→ Uses index_status tool for progress monitoring
```

## 🛠️ Development

### Project Status
- ✅ **NTFS MFT Reader**: Complete using ntfs-reader crate
- ✅ **MCP Server**: Full protocol implementation  
- ✅ **Background Indexing**: Thread-safe concurrent operations
- ✅ **Search Engine**: Pattern matching with filters
- 🔄 **Testing Phase**: Ready for build and performance validation
- 📋 **Duplicate Detection**: Planned feature

### Expected Performance
Based on `ntfs-reader` crate benchmarks:
- **Indexing**: ~4 seconds for millions of files
- **Search**: <100ms response time
- **Memory**: ~400MB for 2M+ files

### Testing
```bash
# Build and test
cargo build --release
cargo test

# Performance benchmark
./target/release/fastsearch --benchmark --drive C

# MCP protocol test
echo '{"method":"initialize","params":{}}' | ./target/release/fastsearch --mcp-server
```

## 🔒 Requirements

### System Requirements
- **Windows 10/11** (NTFS filesystem)
- **Administrator privileges** (for direct MFT access)
- **8GB+ RAM** (recommended for large drives)

### Security Notes
- Requires admin privileges to access raw volume (`\\\\.\\C:`)
- Read-only access - no filesystem modifications
- Graceful permission error handling with fallbacks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

Focus areas:
- Performance optimizations
- Additional search filters
- Cross-platform compatibility
- Duplicate detection algorithms

## 📄 License

MIT License - see LICENSE file

## 🔗 Dependencies

- [`ntfs-reader`](https://lib.rs/crates/ntfs-reader) - NTFS MFT access
- [`serde_json`](https://serde.rs/) - JSON serialization
- [`tokio`](https://tokio.rs/) - Async runtime
- [`clap`](https://clap.rs/) - Command line parsing
- [`anyhow`](https://github.com/dtolnay/anyhow) - Error handling

---

**Built with Rust for maximum performance and safety** ⚡
