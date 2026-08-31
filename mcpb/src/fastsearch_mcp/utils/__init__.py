"""
Utilities for FastSearch MCP.

This module provides various utility functions following FastMCP 2.13 patterns.
"""

from .file_utils import find_files, get_file_info, is_binary_file, search_in_file

__all__ = [
    "find_files",
    "get_file_info",
    "is_binary_file",
    "search_in_file",
]
