# FastSearch MCP - Product Requirements Document (PRD)

**Project**: FastSearch MCP Server  
**Version**: 1.0  
**Date**: July 17, 2025  
**Status**: ✅ **PRODUCTION READY**  
**Team**: Sandra & Claude Development Team  

## 📋 **Executive Summary**

FastSearch MCP is a lightning-fast file search server for Claude Desktop that uses **direct NTFS Master File Table access** to achieve sub-100ms search times without any indexing overhead. It follows the WizFile philosophy of real-time filesystem querying rather than traditional caching approaches.

## 🎯 **Product Vision**

**"Enable Claude Desktop users to search millions of files instantly without waiting for indexing or dealing with stale cached results."**

### **Core Value Proposition**

- **Instant startup** - No indexing delays
- **Always current** - Real-time filesystem state
- **Sub-100ms searches** - Professional-grade performance
- **Minimal resources** - <50MB memory vs GB caches

## 🚨 **NON-NEGOTIABLE ARCHITECTURE PRINCIPLES**

### **CRITICAL: Direct NTFS Approach Only**

The following principles are **ABSOLUTELY NON-NEGOTIABLE** and must never be changed:

#### ❌ **FORBIDDEN PATTERNS**

1. **Background file indexing** - NEVER scan entire drives on startup
2. **In-memory file caching** - NEVER store file lists in RAM
3. **Recursive directory walking** - NEVER traverse folder hierarchies for population
4. **Stale data tolerance** - NEVER return outdated file information
5. **Startup delays** - NEVER require waiting periods before functionality

#### ✅ **REQUIRED PATTERNS**

1. **Direct MFT queries** - ALWAYS read NTFS Master File Table live
2. **Pattern-based search** - ALWAYS search for what's requested, nothing more
3. **Early termination** - ALWAYS stop at max_results limit
4. **Real-time data** - ALWAYS reflect current filesystem state
5. **Instant availability** - ALWAYS be ready immediately after startup

### **Why These Principles Matter**

**Traditional search tools** (Everything, Agent Ransack, Windows Search) work like this:

```
Start → Index drive (10+ min) → Cache files (GB RAM) → Search cache → Stale results
```

**FastSearch MCP** works like WizFile:

```
Search request → Direct NTFS MFT query → Live results (<100ms)
```

This fundamental difference is **what makes FastSearch valuable** and must never be compromised.

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

## 🔧 **Technical Requirements**

### **Performance Specifications**

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Search Latency** | <100ms | 95th percentile, 1M+ files |
| **Memory Usage** | <50MB | Peak RSS during operation |
| **Startup Time** | <1s | Ready to serve requests |
| **Accuracy** | 100% | No false positives/negatives |

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

## 🎨 **User Experience Requirements**

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

## 📊 **Success Metrics**

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

## 🔍 **Quality Assurance**

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
