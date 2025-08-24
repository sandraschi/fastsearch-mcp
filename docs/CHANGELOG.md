# Changelog

All notable changes to the FastSearch MCP project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- GitHub CI/CD workflow for testing and deployment
- Comprehensive README with LLM-friendly documentation

### Changed

- Improved error handling and validation
- Updated documentation to focus on Python implementation

### Fixed

- Resolved type checking and linting errors
- Improved error messages for better debugging

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
