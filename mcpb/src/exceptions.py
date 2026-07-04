"""
Exception classes for FastSearch MCP.

This module defines custom exception classes used throughout the FastSearch MCP codebase.
"""


class McpError(Exception):
    """Base exception class for all MCP-related errors."""

    pass


class ServiceError(McpError):
    """Exception raised for service-related errors."""

    pass


class NtfsError(McpError):
    """Exception raised for NTFS-related errors."""

    pass


class SearchError(McpError):
    """Exception raised for search-related errors."""

    pass


class PipeError(McpError):
    """Exception raised for named pipe communication errors."""

    pass
