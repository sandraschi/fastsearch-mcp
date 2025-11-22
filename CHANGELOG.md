# Changelog

All notable changes to FastSearch MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **SOTA PowerShell error handling** - Comprehensive error handling standards for all scripts
  - Individual error handling per operation (graceful degradation)
  - Retry logic with exponential backoff for transient failures
  - Disk space and path validation before operations
  - Progress reporting for long-running operations
  - Detailed error logging with timestamps and context
  - Integrity verification after critical operations
  - Graceful cleanup on failures
- **Enhanced backup script** - `scripts/backup-repo.ps1` now implements all SOTA patterns
  - Continues with remaining destinations if one fails
  - Configurable retry attempts and delays
  - ZIP integrity verification after creation
  - Error logs saved to temp directory on failures
- **PowerShell standards in .cursorrules** - Mandatory error handling patterns for all new scripts

## [0.5.0] - 2025-11-27

### Added
- **Fast service availability checks** - Optimized from 5 seconds to <1ms per check
  - Fast pipe connection check (fails immediately if service is down)
  - 2-second caching to avoid repeated checks on rapid searches
  - Fallback to process check only if pipe check is ambiguous
- **Improved error messages** - Clear, user-friendly error messages with step-by-step recovery instructions
  - Service-required flags in search responses
  - Tool suggestions for troubleshooting (`service_status`, `start_service`, etc.)
- **Comprehensive test coverage** - 18/18 tests passing
  - Tests for different file patterns (*.py, *.cpp, *.txt, etc.)
  - Tests for different drives (C:\, D:\, etc.)
  - Tests for different start directories
  - Tests for search all drives functionality

### Changed
- **Service checks performance** - Reduced from 5 seconds to <1ms overhead per search
- **Error handling** - More explicit and actionable error messages
- **Search response format** - Added `service_required` flag and `suggestion` field

### Removed
- **Fallback code** - Removed all treewalking fallbacks that violated architecture
  - Removed `_fallback_search()` dead code from `service_client.py`
  - Removed `basic_file_search()` treewalker from `mcp_server.py`
  - Removed `fastsearch.search_basic` tool registration
- **Python fallback references** - Updated all documentation to reflect direct MFT access only

### Fixed
- **Search functionality** - All search tools now fully operational
  - File searches working across different patterns, drives, and directories
  - Service integration complete - FastSearch Windows service running and responding
  - Direct NTFS MFT access verified and working

### Documentation
- Created `CHANGELOG.md` - Project changelog following Keep a Changelog format
- Created `docs/RECENT_IMPROVEMENTS.md` - Comprehensive documentation of recent improvements
- Created `docs/SERVICE_AVAILABILITY_CHECKS.md` - Detailed explanation of service check flow
- Updated `README.md` - Reflects current operational status
- Updated `docs/STATUS_REPORT.md` - Updated with recent improvements and current status
- Updated `docs/TECHNICAL_ARCHITECTURE.md` - Removed fallback references, updated status
- Updated `docs/PRODUCT_REQUIREMENTS.md` - Updated to version 2.2, reflects production-ready status, removed fallback references

## [0.4.0] - 2025-11-15

### Added
- Direct NTFS MFT access implementation
- FastMCP 2.13 compliant MCP server
- Comprehensive tool suite (18 tools)
- Service management tools
- Advanced search with MFT attribute filtering

### Changed
- Architecture to direct MFT access only (no indexing, no caching)

## [0.3.0] - Previous Release

### Added
- Initial MCP bridge implementation
- Basic file search functionality
- Service infrastructure

---

[Unreleased]: https://github.com/yourusername/fastsearch-mcp/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/yourusername/fastsearch-mcp/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/yourusername/fastsearch-mcp/compare/v0.3.0...v0.4.0

