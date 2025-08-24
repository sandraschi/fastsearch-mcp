# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Service Manager Tool**: Comprehensive Windows service management capabilities
  - List services with filtering by status, startup type, and name
  - Start, stop, and restart services
  - View detailed service information
  - Configure service startup types (Automatic, Manual, Disabled, etc.)
  - Access service event logs with advanced filtering

### Changed
- Updated documentation with Service Manager tool usage and examples
- Improved error handling and logging for service operations
- Enhanced async support for long-running service operations

### Fixed
- Fixed issue with service status reporting for services with long display names
- Resolved race condition in service state change operations
- Fixed event log parsing for non-ASCII characters
