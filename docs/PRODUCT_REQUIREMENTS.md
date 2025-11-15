# FastSearch MCP - Product Requirements Document (PRD)

**Project:** FastSearch MCP Server  
**Version:** 2.1  
**Date:** November 10, 2025  
**Status:** 🚧 Service startup diagnostics in progress; MCP bridge production ready

---

## 📋 Executive Summary

FastSearch MCP gives Claude Desktop instant, large-scale file search on Windows by reading the NTFS Master File Table (MFT) on demand. A privileged C++ Windows service performs the MFT scan while a user-mode Python MCP bridge exposes tools to Claude. We explicitly reject traditional indexing, caching, or background scanning so startup stays instant and results remain live.

---

## 🎯 Product Vision

**"Deliver WizFile-class search speed inside Claude Desktop without sacrificing startup time, accuracy, or system stability."**

### Core Value Proposition

- ⚡ **Instant results**: Live NTFS MFT access, no pre-computed index.
- 🧠 **Claude-native**: Structured FastMCP tools with rich schemas and documentation.
- 🔒 **Secure privilege separation**: Elevated C++ service + user-mode MCP bridge.
- 🪶 **Lightweight**: Memory footprint below 50 MB with no persistent stores.
- 🎯 **Precise**: Results always reflect the current filesystem; deleted files never linger.

---

## 🚨 Non-Negotiable Principles

1. **Direct MFT Access Only**
   - Every search must read the NTFS MFT in real time.
   - No background indexing, recursive directory walking, or caching of file metadata.

2. **Instant Startup**
   - Both service and bridge must start in under one second.
   - Service may not perform work until the first request arrives.

3. **Predictable Resource Usage**
   - Peak memory under 50 MB even on multi-million file volumes.
   - No allocations proportional to total file count.

4. **Early Termination**
   - Respect `max_results`; stop scanning as soon as the cap is reached.
   - Honour path and filter constraints before emitting results to the bridge.

5. **Transparent Degradation**
   - If the service is unavailable, the bridge may fall back to Python globbing but must label the response as degraded and encourage restoring direct MFT access.

---

## 🏗 Functional Requirements

### 1. `file_search`
- Input: pattern, optional drive/path filters, `max_results`.
- Processing: stream the NTFS MFT, apply filters, stop at `max_results`.
- Output: ordered list of matches with path, size, timestamps, and method indicator.
- Latency target: < 100 ms on SSD-backed systems for typical patterns.

### 2. `disk_analyzer`
- Identify the largest files/directories on a drive.
- Reuses the MFT stream with size sorting limited to the top N entries.

### 3. `duplicate_finder` (optional/experimental)
- Uses file size + metadata heuristics; may require additional per-file hashing after initial MFT pass (performed lazily, never cached globally).

### 4. Service Management Tools
- `service_status`, `start_service`, `stop_service`, `get_service_logs`, etc. provide operational control and diagnostics.

---

## 🤝 Integration Requirements

### Claude Desktop MCP
- Full FastMCP 2.13 compliance: tool discovery, JSON schema validation, streaming responses.
- Rich documentation metadata so Claude knows how and when to call each tool.
- Clear error signalling for privilege issues or service downtime.

### Diagnostics & Tooling
- PowerShell scripts (`install-service.ps1`, `debug-service-startup.ps1`, `read-service-logs.ps1`) must remain up to date.
- Logs must surface privilege failures, pipe errors, and Event ID 7034 crashes.

---

## 🧩 Technical Requirements

| Domain | Requirement |
|--------|-------------|
| **Service Language** | C++17 (Visual Studio toolchain). |
| **Bridge Language** | Python 3.10+ with `fastmcp` integration. |
| **Privileges** | Service runs as `LocalSystem`; bridge runs as standard user. |
| **IPC** | Named pipe `\\.\pipe\FastSearchMCP` with JSON messages.
| **Filesystem Support** | Windows NTFS volumes. Non-NTFS drives fall back to Python glob with warning. |

### Error Handling
- Service failures must emit Event Log entries and return structured errors to the bridge.
- Bridge responses must include remediation advice (e.g. "Run install-service.ps1 start as Administrator").

### Security
- No sensitive data persisted. Logs include only necessary metadata and error details.
- Pipe ACL restricted to the launching user session.
- No network access.

---

## 📊 Success Metrics

| KPI | Target | Measurement |
|-----|--------|-------------|
| Search latency | < 100 ms (95th percentile, SSD, 1M files) | `tests/test_fastsearch.py` benchmark. |
| Memory usage | < 50 MB at peak | Windows Performance Monitor / internal counters. |
| Startup time | < 1 s for both bridge and service | Stopwatch instrumentation. |
| Accuracy | 100% live filesystem fidelity | Regression tests + manual validation. |
| Fallback visibility | 100% of degraded runs emit warnings | Bridge logs + Claude responses. |

---

## 🧪 Testing Strategy

- **Unit Tests:** pattern parsing, parameter validation, fallback behaviours.
- **Integration Tests:** named pipe contract, service lifecycle scripts, privilege checks.
- **Performance Harness:** repeatable MFT scanning benchmarks (requires elevated PowerShell session).
- **Manual QA:** Event log review, service start/stop cycles, failure injection.

---

## 🛡 Risk Management

| Risk | Mitigation |
|------|------------|
| Service startup crash (Event ID 7034) | Use enhanced logging, `debug-service-startup.ps1`, and staged initialisation. |
| Loss of elevation | Detect quickly, return actionable message, guide user to reinstall/start service. |
| Architecture drift toward indexing | Maintain documentation warnings, enforce during code review, add automated linting for banned patterns if necessary. |
| Cross-user pipe access | Maintain restricted ACLs and verify during install script execution. |

---

## 🔜 Roadmap Highlights

1. **Stabilise service startup** across all supported Windows builds.
2. **Enhance diagnostics** with optional pipe-level tracing (on-demand, not persistent).
3. **Improve fallback messaging** so Claude can offer remediation steps automatically.
4. **Explore additional tools** (e.g. permission reporting) while respecting zero-indexing rules.

---

Keeping the documentation aligned with the C++ service + Python bridge architecture is essential. Any proposal that introduces indexing, caching, or long-running scans must be rejected before implementation.
