# Changelog

All notable changes to the FastSearch MCP project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **MCP 2.12 Compliance**: Full FastMCP 2.12 standard compliance with proper tool registration
- **All 15 Tools Working**: Complete tool suite now functional in Claude Desktop
- **Direct Tool Implementations**: Replaced mock dependencies with working implementations
- **Comprehensive Tool Suite**: 15 production-ready tools including:
  - File search and content search
  - Disk analysis and duplicate detection
  - File integrity checking
  - System resource monitoring
  - Complete Windows service management
  - Comprehensive help system
- **Service Client Module**: Python bridge for C++ service communication
- **Fallback Implementations**: All tools work without requiring C++ service

### Changed
- **Tool Registration**: Migrated from custom registry to FastMCP 2.12 decorator pattern
- **Error Handling**: Enhanced error handling across all tools
- **Service Independence**: Most tools no longer require C++ service to be running
- **Documentation**: Updated README with current production-ready status

### Fixed
- **MCP Compliance**: Removed non-standard `description` and `parameters` from tool registration
- **Tool Dependencies**: Eliminated mock tool system dependencies
- **Service Communication**: Improved service status checking and communication
- **PowerShell Scripts**: Fixed function name conflicts and infinite loop issues

### Security
- **Privilege Separation**: Maintained secure dual-process architecture
- **Input Validation**: Enhanced validation across all tool implementations

## [0.1.0] - 2025-08-03

### Added

- Initial Python MCP implementation with FastMCP 2.10+ support
- Decorator-based LLM documentation system
- DXT packaging with Anthropic standards
- Migrated from Rust bridge to pure Python MCP implementation
- Fixed issues with Windows named pipe communication
- Initial release of FastSearch MCP
- Direct NTFS MFT access for fast file searching
- Privilege-separated architecture for security
- Multi-drive support with hot-swap detection
- Basic search functionality with glob, regex, and exact matching

### Security

- Implemented secure privilege separation between MCP and service
- Input validation for all MCP methods
- Secure communication over Windows named pipes

## [0.0.1] - 2025-07-01

### Added

- Initial project setup
- Basic Rust service implementation
- Proof of concept for MFT access
