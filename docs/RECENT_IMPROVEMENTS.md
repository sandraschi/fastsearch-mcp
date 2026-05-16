# Recent Improvements - May 2026

**Date:** 2026-05-16  
**Status:** ✅ All improvements implemented and tested

## 🔧 Critical Bugfixes (May 2026)

### C++ MFT Parsing Fixes
- **Fixed MFT_RECORD_HEADER struct alignment** - The `WORD Flags` field was at offset 0x26 instead of 0x16. Caused the "record in use" bit check (`header->Flags & 0x0001`) to read the high word of the MFT record number. All records 0-65535 were silently treated as "not in use" and skipped, including on first MFT fragment on fragmented volumes where the estimate only covers the first fragment. Combined effect: **zero search results.**
- **Added USA fixup** - Without applying the Update Sequence Array to each MFT record, the last 2 bytes of every 512-byte sector contained fixup values. These corrupted `$ATTRIBUTE_HEADER.Length` fields when attributes crossed sector boundaries, causing silent parse failures.

### Python Bridge Fixes (14 bugs fixed)
| # | Component | Bug | Impact |
|---|-----------|-----|--------|
| 1 | `mcp_server.py` | Session ID double-popped | All session state lost every request |
| 2 | `pipe_client.py` | Handle leak on pipe error | Kernel handle leak on every I/O error |
| 3 | `pipe_client.py` | Blocking CreateFile in async | Event loop frozen during pipe connect |
| 4 | `service_manager.py` | Args passed character-by-character | Service received garbage arguments |
| 5 | `service_client.py` | Blocking subprocess.run (3 places) | Event loop frozen for up to 30s |
| 6 | `advanced_search.py` | Date parse failures silently dropped | Wrong (unfiltered) results returned |
| 7 | `file_search.py` | Date parse failures silently dropped | Wrong (unfiltered) results returned |
| 8 | `file_name_search.py` | Multi-drive double truncation | Results from later drives discarded |
| 9 | `integrity_checker.py` | New files always "updated" | Wrong status reporting |
| 10 | `search_result_export.py` | CSV/TSV metadata silently dropped | `include_metadata` had no effect |
| 11 | `__main__.py` | ascii:replace encoding | All non-ASCII log output corrupted |
| 12 | `base.py` | bytes decoded as ASCII | Binary data silently corrupted |
| 13 | `api_bridge.py` | UTF-8 truncation → binary | Text files returned as base64 blobs |
| 14 | `tools/__init__.py` | mcp.disable failures hidden | Unwanted tools remained registered |

### 🚀 FastMCP 3.2 Upgrade
- **FastMCP 3.1 → 3.2** - Dependency updated to `fastmcp>=3.2.0,<4`
- **Sampling**: Tools use `ctx: Context = None` injection for client-side LLM sampling via `ctx.sampling()`
- **CodeMode**: `--agentic` flag enables `CodeMode().attach(mcp)` for discovery + execute meta-tools
- **Prompts**: 3 `@mcp.prompt()` templates (search guide, disk analysis, troubleshooting) auto-registered
- **Skills**: 3 `@mcp.skill()` definitions (recent files, cleanup, forensic audit) auto-registered

### ⚡ Performance
- **Async safety** - All blocking Win32 and subprocess calls now properly wrapped in executors/threads, preventing event loop starvation during pipe connection, service queries, and searches.

## Previous: November 2025 Improvements

**Date:** 2025-11-27  
**Status:** ✅ All improvements implemented and tested

## 🎉 Major Milestone: Search Functionality Fully Operational

### ✅ Search Tools Working
- **All search patterns tested** - *.py, *.cpp, *.txt, and more working correctly
- **Multi-drive support** - Searches work across C:, D:, and all NTFS drives
- **Directory searches** - Works with any start directory
- **18/18 comprehensive tests passing** - All search scenarios validated
- **Service integration complete** - FastSearch Windows service running and responding

### Test Results
```
✅ Basic Search - *.py (C:\) - PASSED
✅ C++ File Search - *.cpp (D:\) - PASSED  
✅ D: Drive - *.py Search - PASSED
✅ Extension Length Test - PASSED
✅ Search All Drives - *.txt - PASSED
✅ Advanced Search - Size Filter - PASSED
✅ Advanced Search - Date Filter - PASSED
✅ Advanced Search - Combined Filters - PASSED
✅ Speed Benchmark - PASSED
... (18/18 tests passing)
```

## ⚡ Performance Optimizations

### Fast Service Checks (<1ms)
**Problem:** Service availability check was taking up to 5 seconds using `tasklist` command.

**Solution:**
- Fast pipe connection check first (fails immediately if service is down)
- 2-second caching to avoid repeated checks on rapid searches
- Fallback to process check only if pipe check is ambiguous

**Results:**
- First check: ~0.1ms (pipe connection)
- Cached checks: ~0.01ms (essentially instant)
- Old approach: up to 5 seconds ❌
- New approach: <1ms ✅

**Impact:** Service check adds negligible overhead to each search, maintaining the "FastSearch" performance promise.

## 🧹 Architecture Cleanup

### Removed Fallback Code
**Rationale:** Treewalking fallbacks violate the architecture (direct MFT access only).

**Removed:**
- `_fallback_search()` - Dead code that was never called
- `basic_file_search()` - Treewalker using `os.walk()` 
- `fastsearch.search_basic` - Tool registration for fallback search

**Result:** Clean architecture with direct MFT access only. No compromises, no fallbacks.

## 📝 Improved Error Messages

### User-Friendly Error Messages
**Before:** Technical error messages that didn't help users fix the issue.

**After:** Clear, formatted error messages with:
- Step-by-step recovery instructions
- References to available tools (`service_status`, `start_service`, etc.)
- Service-required flags in search responses
- Actionable troubleshooting steps

**Example Error Message:**
```
❌ FastSearch service is not running.

The FastSearch MCP requires the FastSearch Windows service to be installed and running
for direct NTFS MFT access. Without the service, file searches cannot be performed.

To fix this:
1. Check if the service is installed: Open Windows Services (Win+R → services.msc)
2. Look for 'FastSearch MCP Service' or 'FastSearchMCP' in the list
3. If installed but stopped: Right-click → Start
4. If not installed: Run the installer as administrator

You can also use the 'service_status' tool to check the current service status.
```

## 📄 Enhanced Export Tool with Pandoc Support

### New Export Formats
**Added**: Professional document export formats via Pandoc integration.

**New Formats Available**:
- **PDF** - Professional PDF reports
- **Word (DOCX)** - Editable Word documents
- **HTML** - Web-ready HTML reports
- **EPUB** - E-book format
- **ODT** - OpenDocument Text
- **RTF** - Rich Text Format
- **LaTeX** - LaTeX source documents

**Implementation**:
- Automatic Pandoc detection (checks availability before use)
- Graceful fallback with clear error messages if Pandoc unavailable
- Standard formats (CSV, JSON, Markdown, TSV) work without dependencies
- Pandoc formats require `output_path` (file output only)
- 60-second timeout for conversions
- Temporary file cleanup after conversion

**Benefits**:
- Professional document generation for reports
- Multiple format options for different use cases
- No breaking changes - standard formats unchanged
- Optional enhancement - works without Pandoc

**Example Usage**:
```python
# Export to PDF (requires Pandoc)
export = await search_result_export(
    results["results"],
    export_format="pdf",
    output_path="C:\\temp\\report.pdf"
)

# Export to Word (requires Pandoc)
export = await search_result_export(
    results["results"],
    export_format="docx",
    output_path="C:\\temp\\report.docx"
)
```

## Live Tests and Tests Page (March 2025)

### Live Integration Tests
- **`fastsearch_mcp.live_tests.run_live_tests()`** runs four steps: service_process (cached check), pipe_connect (ping), get_service_info (via pipe), search_via_pipe (real search with configurable pattern/directory/max_results).
- **Pytest:** `tests/test_live_pipe.py` runs the same flow; marked `@pytest.mark.integration`, `@pytest.mark.service`, Windows-only. Run with service up: `pytest tests/test_live_pipe.py -v`.
- **API:** `POST /api/tests/run` with optional body `{ pattern, directory, max_results }` returns `{ passed, total, results }` for the webapp.

### Tests Page in Webapp
- **Route:** `/tests`. Sidebar link "Tests" (FlaskConical icon).
- **UI:** Configurable pattern, directory, max_results; "Run tests" button; result list with pass/fail, message, duration, expandable JSON details.
- Enables live verification of pipe and search without leaving the dashboard.

### Path Normalization and Pipe Error Handling
- **Path normalization:** User input like `C:` is normalized to `C:\\` before sending to the C++ service to avoid empty results from path format mismatch.
- **Pipe errors:** When the pipe fails to connect or Windows API is unavailable, the pipe client now returns an `error` key so the service client raises and the UI shows a clear error instead of "success, 0 results".

## 📊 Summary

| Improvement | Status | Impact |
|------------|--------|--------|
| Search functionality | ✅ Working | All patterns, drives, directories tested |
| Service checks | ✅ Optimized | <1ms overhead (from 5 seconds) |
| Architecture cleanup | ✅ Complete | No fallbacks, direct MFT only |
| Error messages | ✅ Improved | Clear, actionable guidance |
| Test coverage | ✅ Complete | 18/18 tests passing |
| Export tool enhancement | ✅ Complete | Pandoc support added, 7 new formats |
| Live tests + Tests page | ✅ Complete | Pipe + real search tests in pytest and webapp |
| Path normalization | ✅ Complete | C: → C:\\ for service compatibility |
| Pipe error reporting | ✅ Fixed | No more success with 0 results when pipe fails |

## 🎯 Next Steps

- ✅ Search functionality operational
- ✅ Performance optimized
- ✅ Architecture cleaned up
- ✅ Error messages improved
- ✅ Live tests and Tests page added
- 🔄 Continue monitoring service stability
- 🔄 Add more comprehensive test scenarios as needed

---

**All improvements have been tested and verified. FastSearch MCP is production-ready with fully operational search functionality.**

