# FastSearch MCP - Product Requirements Document (PRD)

**Project**: FastSearch MCP Server  
**Version**: 2.0  
**Date**: August 30, 2025  
**Status**: 🚀 **HIGH-PERFORMANCE C++ IMPLEMENTATION**  
**Team**: Sandra & Claude Development Team  

## 📋 **Executive Summary**

FastSearch MCP is a high-performance file search server for Claude Desktop that leverages **direct NTFS Master File Table access** with advanced memory-mapped I/O to achieve **1M+ files/second** search speeds. The new C++ implementation provides enterprise-grade performance with minimal resource usage.

## 🎯 **Product Vision**

**"Enable Claude Desktop users to search millions of files instantly without waiting for indexing or dealing with stale cached results."**

### **Core Value Proposition**

- **Blazing fast** - 1M+ files/second scanning speed
- **Memory efficient** - ~10MB per 1M files
- **Multi-threaded** - Scales with CPU cores (up to 16 threads)
- **Zero latency** - In-memory caching of frequent queries
- **Always current** - Real-time filesystem state
- **Minimal footprint** - <100MB memory even for 100M+ files

## 🚨 **CORE ARCHITECTURE PRINCIPLES**

### **CRITICAL: High-Performance NTFS Access**

The following principles define our high-performance architecture:

#### ⚡ **PERFORMANCE FOCUSED**

1. **Memory-mapped I/O** - Direct MFT access with zero-copy operations
2. **Lock-free algorithms** - Minimize thread contention
3. **Parallel processing** - Multi-threaded MFT scanning (16+ threads)
4. **Efficient caching** - Smart LRU cache for frequent queries
5. **Minimal overhead** - No background processes or indexing

#### ✅ **REQUIRED PATTERNS**

1. **Direct MFT access** - Memory-mapped I/O for maximum throughput
2. **Thread-safe design** - Lock-free where possible, fine-grained locks otherwise
3. **Efficient memory use** - Custom allocators and memory pools
4. **Early termination** - Stop processing at max_results limit
5. **Real-time data** - Always reflect current filesystem state

### **Why This Architecture Matters**

**Traditional search tools** (Everything, Agent Ransack, Windows Search) work like this:

```
Start → Index drive (10+ min) → Cache files (GB RAM) → Search cache → Stale results
```

**FastSearch MCP** works like WizFile but faster:

```
Search request → Parallel MFT scan (1M+/sec) → Live results (sub-100ms)
```

**Key advantages**:

- **10-100x faster** than traditional tools
- **1/10th the memory** usage
- **Real-time accuracy** - no stale results
- **Instant startup** - no waiting for indexing

## 🏗️ **Functional Requirements**

### **Core Features**

#### **1. Fast Search Tool**

- **Input**: File pattern (*.js, config.*, README, etc.)
- **Processing**: Direct NTFS MFT scan with pattern matching
- **Output**: List of matching files with metadata
- **Performance**: <100ms for 1M+ file filesystems
- **Accuracy**: 100% current filesystem state

#### **2. Large File Discovery**

- **Input**: Minimum size threshold (e.g., 100MB)
- **Processing**: MFT scan with size filtering and sorting
- **Output**: Largest files on system, sorted by size
- **Use Case**: Disk cleanup, storage analysis

#### **3. Performance Benchmarking**

- **Input**: Drive selection and test patterns
- **Processing**: Systematic search performance measurement
- **Output**: Timing statistics and throughput metrics
- **Use Case**: Performance validation and optimization

### **Integration Requirements**

#### **Claude Desktop MCP Protocol**

- **JSON-RPC 2.0** compliance for tool invocation
- **Tool discovery** via MCP tools/list endpoint
- **Error handling** with appropriate status codes
- **Documentation** embedded in tool schemas

#### **Web API (Optional)**

- **HTTP REST interface** for frontend integration
- **CORS support** for browser-based clients
- **JSON responses** with consistent error formatting
- **Health checks** for monitoring

## **Technical Requirements**

### **Performance Requirements**

| Metric | Target |
|--------|--------|
| Search Speed | 1M+ files/second |
| Memory Usage | ~100MB base + 10MB/1M files |
| Threads | 1-16 (auto-scaling) |
| Cache Size | Configurable, default 1M entries |
| Disk I/O | Memory-mapped MFT access only |

### **Resource Utilization**

- **CPU**: Scales linearly with core count
- **Memory**: Predictable, bounded usage
- **Disk**: Minimal, sequential MFT reads
- **Network**: Efficient binary protocol

### **System Requirements**

#### **Windows (Primary Platform)**

- **OS**: Windows 10/11 (NTFS required)
- **Privileges**: Administrator access for MFT reading
- **Dependencies**: Rust toolchain, ntfs crate
- **Architecture**: x64 (primary), x86 (optional)

#### **Cross-Platform (Future)**

- **Linux**: ext4 metadata access (future enhancement)
- **macOS**: APFS support (future enhancement)
- **Fallback**: Filesystem walk for non-NTFS systems

### **Security Requirements**

#### **Privilege Management**

- **NTFS Access**: Requires admin privileges for volume access
- **Error Handling**: Graceful degradation without admin rights
- **Sandboxing**: Runs within Claude Desktop security context
- **Input Validation**: Sanitize all search patterns and paths

#### **Data Protection**

- **No data storage** - Never cache file contents or metadata
- **Privacy**: Only accesses file metadata, not content
- **Logging**: Minimal logging, no sensitive data retention

## **User Experience Requirements**

### **Claude Desktop Integration**

#### **Tool Discoverability**

- **Clear tool names** - `fast_search`, `find_large_files`, `benchmark_search`
- **Descriptive schemas** - Self-documenting parameter descriptions
- **Usage examples** - Built-in help and examples

#### **Response Quality**

- **Structured output** - Consistent formatting across tools
- **Performance feedback** - Include search timing in results
- **Progress indication** - Show search progress for longer operations
- **Error clarity** - Clear error messages with actionable advice

### **Search Experience**

#### **Pattern Matching**

- **Glob patterns** - Standard wildcard support (*.js, config.*)
- **Exact matching** - Support for precise filename searches
- **Case handling** - Case-insensitive by default
- **Special characters** - Proper escaping and handling

#### **Result Presentation**

- **Relevance ordering** - Most relevant results first
- **Metadata display** - File size, path, type information
- **Path formatting** - Clear, readable path presentation
- **Truncation handling** - Appropriate handling of long result lists

## **Success Metrics**

### **Performance KPIs**

- **Search latency**: 95% of searches complete in <100ms
- **Memory efficiency**: <50MB peak memory usage
- **Startup speed**: Ready in <1 second
- **Accuracy rate**: 100% (no missed or phantom files)

### **User Experience KPIs**

- **Claude integration**: Seamless tool discovery and invocation
- **Error rate**: <1% failed searches due to system issues
- **User satisfaction**: Fast, accurate results without indexing delays

### **Technical KPIs**

- **Code quality**: Clean compilation with minimal warnings
- **Maintainability**: Clear architecture with focused responsibilities
- **Documentation**: Comprehensive docs preventing architecture drift

## **Quality Assurance**

### **Testing Requirements**

#### **Unit Testing**

- **Pattern matching** - Verify glob-to-regex conversion
- **NTFS reading** - Test MFT access with various file types
- **Error handling** - Validate graceful failure modes
- **Performance** - Benchmark critical code paths

#### **Integration Testing**

- **MCP protocol** - Verify Claude Desktop compatibility
- **Web API** - Test HTTP interface functionality
- **Cross-platform** - Validate fallback mechanisms

#### **Performance Testing**

- **Load testing** - Large filesystem performance
- **Memory profiling** - Verify no memory leaks
- **Latency testing** - Confirm <100ms targets
- **Stress testing** - Behavior under high search volumes

### **Documentation Requirements**

#### **Architecture Documentation**

- **NTFS approach explanation** - Why direct MFT access matters
- **WizFile comparison** - Competitive analysis and positioning
- **Performance characteristics** - Detailed benchmarking data
- **Design decisions** - Rationale for architectural choices

#### **Developer Documentation**

- **Setup guide** - Clear installation and configuration
- **API reference** - Complete tool and endpoint documentation
- **Troubleshooting** - Common issues and solutions
- **Contribution guide** - How to maintain architecture principles

## 🛡️ **Risk Management**

### **Technical Risks**

#### **NTFS API Dependency**

- **Risk**: Changes to Windows NTFS access APIs
- **Mitigation**: Use stable, well-maintained ntfs crate
- **Fallback**: Filesystem walk for degraded functionality

#### **Performance Regression**

- **Risk**: Accidental addition of indexing or caching
- **Mitigation**: Strict code review and architectural principles
- **Detection**: Continuous performance monitoring

#### **Privilege Requirements**

- **Risk**: Users unable to grant admin access
- **Mitigation**: Clear documentation and graceful degradation
- **Alternative**: Limited functionality with standard privileges

### **Market Risks**

#### **Competitive Positioning**

- **Risk**: Users preferring traditional indexed search tools
- **Mitigation**: Clear communication of instant startup benefits
- **Differentiation**: Focus on Claude Desktop integration advantage

#### **Platform Limitations**

- **Risk**: NTFS-only approach limiting cross-platform adoption
- **Mitigation**: Future roadmap for ext4/APFS support
- **Positioning**: Windows-first, expansion later

## 🚀 **Success Criteria**

### **Launch Readiness**

- ✅ **Clean compilation** - No errors, minimal warnings
- ✅ **MCP protocol compliance** - Full Claude Desktop integration
- ✅ **Performance targets** - <100ms search times achieved
- ✅ **Documentation complete** - All required docs written
- ✅ **Testing complete** - Unit, integration, and performance tests pass

### **Post-Launch Success**

- **User adoption** - Active usage within Claude Desktop community
- **Performance maintenance** - Sustained <100ms performance
- **Zero architecture drift** - No accidental addition of indexing
- **Community contribution** - External contributions following principles

---

## 🎯 **The Bottom Line**

FastSearch MCP's value proposition is **instant file search without indexing delays**. This is achieved through **direct NTFS Master File Table access**, following the proven WizFile approach.

**Any deviation from this architecture destroys the product's value proposition.**

The principles outlined in this PRD are non-negotiable and must be maintained by all contributors, including AI coding assistants that might try to "optimize" the code by adding traditional indexing patterns.

**FastSearch MCP: Because searching shouldn't require indexing.** 🚀
