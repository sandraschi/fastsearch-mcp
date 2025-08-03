---
title: FastSearch MCP Server - Project Plan
type: note
permalink: projects-fast-search-mcp-server-project-plan
---

# FastSearch MCP Server - Project Plan by Sandra & Claudius

**Project**: Lightning-fast file search using NTFS Master File Table  
**Inspiration**: WizFile-style performance  
**Authors**: Sandra & Claudius  
**Date**: July 15, 2025  

## 🎯 Project Overview

**Problem**: Current filesystem search tools are painfully slow

- Claude's filesystem search takes forever on large directories
- Basic Memory's file scanning struggles with 100,000+ files
- Windows Explorer search is terrible
- Need instant search like WizFile/Everything

**Solution**: FastSearch MCP server that reads NTFS Master File Table directly

- Instant results for millions of files
- Real-time updates as files change
- Multiple search modes (name, content, attributes)
- Blazing fast like WizFile but with MCP integration

## 🚀 Why This Matters

### Current Pain Points

1. **Basic Memory Performance**: Scanning node_modules takes 15+ minutes
2. **Development Workflow**: Finding files in large codebases is slow
3. **Claude Integration**: Filesystem tools are the weakest link
4. **Daily Productivity**: Waiting for file searches breaks flow

### Target Performance

- **WizFile baseline**: 2+ million files indexed in <3 seconds
- **Target**: Sub-second search through entire drive
- **Memory usage**: Minimal (few hundred MB for millions of files)
- **Updates**: Real-time as files change

## 🔧 Technical Architecture

### Core Components

#### 1. NTFS MFT Reader

```
Language: Rust (for speed + safety)
Dependencies:
- winapi-rs for Windows API access
- ntfs crate for MFT parsing
- serde for serialization
```

**Key Functions**:

- Read Master File Table directly
- Parse file records without filesystem API overhead
- Handle NTFS permissions and access rights
- Support UNC paths and network drives

#### 2. Index Engine

```
In-memory B-tree structure:
- File paths → metadata mapping
- Trigram indexing for partial matches
- Size/date/attribute indexes
- Content hash cache for duplicates
```

**Features**:

- Incremental updates via USN Journal
- Multiple index types (name, size, date, type)
- Memory-mapped files for large datasets
- Persistent cache with fast startup

#### 3. MCP Server Interface

```
Tools provided:
- fast_search(pattern, filters)
- find_by_size(min_size, max_size)
- find_by_date(after, before)
- find_duplicates(hash_content)
- watch_changes(path)
```

**Integration**:

- Standard MCP protocol
- JSON-RPC over stdio
- Streaming results for large result sets
- Progress reporting for long operations

### Search Modes

#### 1. Name Search

```rust
// Instant filename matching
fast_search("*.js", filters: {
    path: "D:\\dev",
    exclude: ["node_modules", ".git"],
    max_results: 1000
})
```

#### 2. Content Search

```rust
// File content indexing (optional)
search_content("TODO FIXME", filters: {
    file_types: [".rs", ".py", ".js"],
    max_file_size: "10MB"
})
```

#### 3. Attribute Search

```rust
// Search by file attributes
find_large_files(min_size: "100MB", filters: {
    older_than: "30 days",
    file_types: [".log", ".tmp"]
})
```

## 📋 Implementation Plan

### Phase 1: Core MFT Reader (2-3 weeks)

**Goal**: Read NTFS MFT and build basic file index

#### Week 1: NTFS Foundation

- [ ] Set up Rust project with ntfs/winapi dependencies
- [ ] Implement basic MFT record reading
- [ ] Parse file names and basic attributes
- [ ] Handle different record types (files, directories, etc.)

#### Week 2: Index Building

- [ ] Build in-memory file tree structure
- [ ] Implement efficient path storage (deduplicated)
- [ ] Add basic filtering (size, date, type)
- [ ] Performance testing on large drives

#### Week 3: MCP Integration

- [ ] Implement MCP server protocol
- [ ] Add basic search tools
- [ ] JSON serialization for results
- [ ] Error handling and edge cases

### Phase 2: Advanced Features (2-3 weeks)

**Goal**: Real-time updates and advanced search

#### Week 4: USN Journal Integration

- [ ] Monitor filesystem changes via USN Journal
- [ ] Implement incremental index updates
- [ ] Handle file moves, renames, deletions
- [ ] Optimize update performance

#### Week 5: Advanced Search

- [ ] Trigram indexing for partial matches
- [ ] Regular expression support
- [ ] Content indexing for small files
- [ ] Duplicate detection by hash

#### Week 6: Optimization & Polish

- [ ] Memory usage optimization
- [ ] Startup time improvements
- [ ] Configuration file support
- [ ] Comprehensive testing

### Phase 3: Production Ready (1-2 weeks)

**Goal**: Deployment and integration

#### Week 7: Packaging

- [ ] Windows installer/distribution
- [ ] Claude Desktop integration
- [ ] Configuration UI (optional)
- [ ] Documentation and examples

#### Week 8: Integration Testing

- [ ] Test with Basic Memory
- [ ] Performance benchmarking vs WizFile
- [ ] Large dataset testing (millions of files)
- [ ] Bug fixes and optimizations

## 🛠️ Technical Challenges

### 1. NTFS Access Permissions

**Challenge**: Need admin rights to read MFT directly
**Solutions**:

- Fallback to filesystem API for non-admin users
- Request elevation on first run
- Use Windows Service for background indexing

### 2. Memory Management

**Challenge**: Millions of file records = lots of memory
**Solutions**:

- String interning for common path components
- Compressed file record storage
- Memory-mapped index files for persistence

### 3. Cross-Platform Support

**Challenge**: NTFS MFT is Windows-specific
**Solutions**:

- Start with Windows-only implementation
- Add Linux/macOS filesystem equivalents later
- Abstract interface for different filesystem types

### 4. Real-time Updates

**Challenge**: Keeping index synchronized with filesystem
**Solutions**:

- USN Journal for NTFS change monitoring
- Periodic full rescans as backup
- Graceful handling of missed changes

## 📊 Performance Targets

### Baseline Comparisons

- **WizFile**: 2.4M files in 2.8 seconds
- **Everything**: 3.1M files in 4.2 seconds  
- **Windows Search**: Don't even ask 😅

### FastSearch Targets

- **Initial scan**: <5 seconds for 2M files
- **Search response**: <100ms for any query
- **Memory usage**: <500MB for 5M files
- **Update latency**: <1 second for file changes

### Use Case Performance

```
Scenario: Find all .js files in node_modules
- Current filesystem search: 30+ seconds
- FastSearch target: <50ms

Scenario: Find files >100MB modified today
- Current approach: Minutes of scanning
- FastSearch target: <200ms

Scenario: Find duplicate files by content
- Current tools: Hours for large drives
- FastSearch target: <10 minutes (with content hashing)
```

## 🎨 User Experience

### MCP Tool Interface

```json
{
  "name": "fast_search",
  "description": "Lightning-fast file search using NTFS MFT",
  "inputSchema": {
    "type": "object",
    "properties": {
      "pattern": { "type": "string", "description": "File pattern (*.js, README*, etc.)" },
      "path": { "type": "string", "description": "Root path to search" },
      "max_results": { "type": "integer", "default": 1000 },
      "filters": {
        "type": "object",
        "properties": {
          "exclude_dirs": { "type": "array", "items": { "type": "string" } },
          "min_size": { "type": "string" },
          "max_size": { "type": "string" },
          "modified_after": { "type": "string" },
          "file_types": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

### Claude Integration Examples

```
"Find all TypeScript files larger than 100KB in my project"
→ fast_search("*.ts", filters: {min_size: "100KB", path: "D:\\dev\\myproject"})

"Show me all log files modified today"  
→ fast_search("*.log", filters: {modified_after: "today"})

"Find duplicate images in my Photos folder"
→ find_duplicates(path: "C:\\Users\\Sandra\\Photos", file_types: [".jpg", ".png"])
```

## 🔄 Integration Strategy

### Basic Memory Integration

- Replace slow filesystem scanning with FastSearch
- Instant file discovery for project indexing
- Real-time updates when files change
- Exclude patterns handled efficiently

### Claude Desktop Integration

- Add FastSearch to default MCP servers
- Configuration through Claude settings
- Background indexing on startup
- Status indicators for index progress

### Development Workflow

- Use for rapid codebase navigation
- Find files across multiple projects instantly
- Locate config files, logs, dependencies
- Clean up build artifacts and temp files

## 🎯 Success Metrics

### Technical Metrics

- **Search speed**: <100ms for any query
- **Index build**: <10 seconds for 1M files
- **Memory efficiency**: <1KB per file record
- **Update latency**: <1 second for changes

### User Experience Metrics

- **Adoption**: Used in >90% of file search scenarios
- **Satisfaction**: Faster than any alternative tool
- **Reliability**: <1% failure rate on supported filesystems
- **Integration**: Seamless Claude Desktop experience

### Business Value

- **Productivity**: 50%+ faster file operations
- **Developer flow**: Reduced context switching
- **System efficiency**: Lower CPU/disk usage
- **Competitive advantage**: Best-in-class search performance

---

## 🚀 Getting Started

### Prerequisites

- Windows 10/11 (NTFS filesystem)
- Rust development environment
- Admin privileges for MFT access
- 2-4GB RAM for large file indexes

### Development Setup

```bash
# Clone and set up project
git clone https://github.com/sandra-claudius/fastsearch-mcp
cd fastsearch-mcp

# Install Rust dependencies
cargo build

# Run tests
cargo test

# Start MCP server
cargo run --release -- --mcp-server
```

### Quick Test

```bash
# Test basic functionality
echo '{"method": "fast_search", "params": {"pattern": "*.rs"}}' | ./fastsearch-mcp
```

---

**This is our shot at building the fastest file search tool ever integrated with Claude. Time to make filesystem searches instant! 🚀**
