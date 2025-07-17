# FastSearch MCP Server 🚀

**Lightning-fast file search for Claude Desktop using direct NTFS Master File Table access**

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/sandraschi/fastsearch-mcp)
[![Performance](https://img.shields.io/badge/search-<100ms-green.svg)](docs/benchmarks.md)
[![Memory](https://img.shields.io/badge/memory-optimized-blue.svg)](docs/architecture.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🎯 **The FastSearch Philosophy: Direct NTFS Approach**

FastSearch MCP is **NOT** a traditional file search tool. It follows the **WizFile philosophy** of **direct NTFS Master File Table querying** instead of slow, memory-hungry file indexing.

### ❌ **What FastSearch Does NOT Do (By Design)**
- **NO background file indexing** - We don't cache millions of files in RAM
- **NO startup delays** - No waiting 10+ minutes for drive scanning  
- **NO recursive directory walking** - We don't traverse folders like Explorer
- **NO stale cached results** - Every search reads live filesystem state

### ✅ **What FastSearch DOES Do (The WizFile Way)**
- **DIRECT MFT QUERIES** - Each search reads NTFS Master File Table live
- **SUB-100MS SEARCHES** - Instant results without any indexing overhead
- **ALWAYS CURRENT** - Real-time filesystem state, never stale cache
- **MINIMAL MEMORY** - Uses <50MB instead of gigabytes of cached data

## 🔥 **Why This Architecture Matters**

Traditional search tools (Everything, Agent Ransack, etc.) work like this:
```
Startup → Index entire drive (10+ min) → Cache in RAM (GB) → Search cache
```

**FastSearch works like WizFile**:
```
Search request → Query NTFS MFT directly → Return results (<100ms)
```

This means:
- ⚡ **Instant startup** - Ready immediately
- 🎯 **Always accurate** - Never shows deleted files or misses new ones
- 💾 **Memory efficient** - No massive file caches
- 🚀 **Blazing fast** - Direct hardware-level filesystem access

## 🛠️ **Installation**

### Quick Start with Claude Desktop

1. **Install FastSearch MCP**:
   ```bash
   npm install -g fastsearch-mcp
   ```

2. **Add to Claude Desktop** (`claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "fastsearch": {
         "command": "fastsearch-mcp",
         "args": ["--mcp-server"]
       }
     }
   }
   ```

3. **Restart Claude Desktop** and start searching!

### Manual Installation

```bash
git clone https://github.com/sandraschi/fastsearch-mcp.git
cd fastsearch-mcp
cargo build --release
```

**Note**: Requires **Administrator privileges** on Windows for NTFS Master File Table access.

## 🔌 **Dual Interface Design**

FastSearch MCP provides **two interfaces** for maximum flexibility and adoption:

### **Interface 1: MCP Protocol** (Primary)
- **Purpose**: Claude Desktop integration
- **Protocol**: JSON-RPC 2.0 over stdin/stdout
- **Best for**: AI assistant workflows, conversational search, tool discovery

### **Interface 2: HTTP REST API** (Secondary)
- **Purpose**: Web/app integration
- **Protocol**: HTTP REST with JSON
- **Best for**: Dashboards, mobile apps, microservices, CI/CD pipelines

### **Why Dual Interface?**
✅ **Maximum market reach** - MCP + universal HTTP
✅ **Use case optimization** - Right tool for right job
✅ **Risk mitigation** - Protocol independence
✅ **Professional positioning** - Enterprise-ready

**This isn't duplication - it's smart architecture that expands utility with minimal overhead!**

## 🚀 **Usage Examples**

### Basic File Search
```
Find all JavaScript files:
Pattern: *.js
Result: Instant list of all .js files on your system
```

### Advanced Pattern Matching
```
Find configuration files:
Pattern: config.*
Result: config.json, config.yaml, config.ini, etc.
```

### Path-Filtered Search
```
Find React components:
Pattern: *.jsx
Path: components
Result: All JSX files in folders containing "components"
```

### Large File Discovery
```
Find files over 100MB:
Tool: find_large_files
Result: Sorted list of largest files on your system
```

## 🔧 **MCP Tools Available**

### 1. `fast_search` - Lightning-Fast File Search
```json
{
  "pattern": "*.py",
  "path": "projects", 
  "drive": "C",
  "max_results": 1000
}
```

### 2. `find_large_files` - Large File Discovery
```json
{
  "min_size_mb": 100,
  "drive": "C",
  "max_results": 50
}
```

### 3. `benchmark_search` - Performance Testing
```json
{
  "drive": "C"
}
```

## 🏗️ **Technical Architecture**

### Core Components
- **NTFS MFT Reader** - Direct Windows volume access
- **Pattern Engine** - Glob-to-regex conversion with early termination
- **MCP Server** - Protocol-compliant Claude Desktop integration
- **Web API** - Optional HTTP interface for frontend integration

### Performance Optimizations
- **Early termination** - Stops searching when max_results reached
- **Path pruning** - Skips irrelevant directory branches
- **Pattern optimization** - Efficient regex compilation and matching
- **Memory management** - Zero file caching, minimal allocations

## 📊 **Benchmarks**

| Search Type | Average Time | Memory Usage | Files Scanned |
|-------------|--------------|--------------|---------------|
| `*.exe` | 45ms | 12MB | 1M+ files |
| `config.*` | 23ms | 8MB | 1M+ files |
| `*.js` in `src` | 15ms | 5MB | 500K files |

*Benchmarks on Windows 11, NVMe SSD, 1M+ indexed files*

## 🚨 **CRITICAL: For Developers & AI Assistants**

### **DO NOT "FIX" THESE APPARENT "ISSUES"**

If you're using Cursor IDE, GitHub Copilot, or other AI coding assistants, **DO NOT** try to "fix" these characteristics:

❌ **"No background indexing"** - THIS IS INTENTIONAL  
❌ **"No file cache"** - THIS IS THE ARCHITECTURE  
❌ **"Searches take processing time"** - WRONG, they're <100ms  
❌ **"Missing startup file scanning"** - THIS IS THE POINT  

### **Non-Negotiable Architecture Principles**

1. **NEVER add background file indexing**
2. **NEVER cache file lists in memory**
3. **NEVER use recursive directory walking for initial population**
4. **ALWAYS query NTFS MFT directly for each search**
5. **ALWAYS implement early termination at max_results**

**This is a DIRECT NTFS SEARCH TOOL, not a traditional indexed search engine.**

## 🔍 **How It Works: The NTFS Master File Table**

The NTFS Master File Table (MFT) is a special file that contains metadata about every file and directory on an NTFS volume. Instead of walking through directories like Windows Explorer, FastSearch reads this table directly.

### Advantages:
- **Complete filesystem view** - Single source of truth for all files
- **Constant-time access** - No dependency on directory structure depth
- **Always current** - Reflects real-time filesystem state
- **Hardware optimized** - Leverages NTFS design for maximum speed

### WizFile Comparison:
FastSearch MCP uses the same approach as WizFile, the fastest Windows file search tool:
- Direct MFT access
- No indexing overhead  
- Sub-100ms search times
- Minimal memory footprint

## 📁 **Project Structure**

```
fastsearch-mcp/
├── src/
│   ├── main.rs           # Entry point and CLI
│   ├── mcp_server.rs     # MCP protocol implementation
│   ├── ntfs_reader.rs    # Direct NTFS MFT access
│   ├── web_api.rs        # Optional HTTP API
│   └── lib.rs            # Library exports
├── frontend/             # Web interface (optional)
├── docs/                 # Comprehensive documentation
│   ├── ARCHITECTURE.md   # Technical deep-dive
│   ├── BENCHMARKS.md     # Performance analysis
│   └── WIZFILE_COMPARISON.md
├── Cargo.toml           # Rust dependencies
├── package.json         # NPM packaging
└── README.md           # This file
```

## 🔗 **Documentation**

- **[Technical Architecture](docs/ARCHITECTURE.md)** - Deep dive into NTFS MFT access
- **[Performance Guide](docs/BENCHMARKS.md)** - Optimization techniques and benchmarks
- **[WizFile Comparison](docs/WIZFILE_COMPARISON.md)** - Feature and performance analysis
- **[MCP Protocol](docs/MCP_PROTOCOL.md)** - Integration specifications
- **[API Reference](docs/API_REFERENCE.md)** - Complete tool documentation

## 🤝 **Contributing**

Before contributing, please read our [Architecture Principles](docs/ARCHITECTURE.md) to understand why FastSearch uses direct NTFS access instead of traditional indexing.

Key areas for contribution:
- Cross-platform MFT equivalent support (ext4, APFS)
- Advanced pattern matching algorithms
- Performance optimizations
- Documentation improvements

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- Inspired by WizFile's direct NTFS approach
- Built for the Claude Desktop MCP ecosystem
- Powered by the Rust NTFS crate for safe Windows volume access

---

**FastSearch MCP: Because searching shouldn't require indexing** 🚀