"""FastSearch MCP - Lightning-fast file search for Claude Desktop.

This package provides a FastMCP 2.10+ compliant MCP server for fast file searching
using direct NTFS Master File Table access.
"""

__version__ = "0.1.0"
__all__ = ["McpServer"]

from .mcp_server import McpServer
