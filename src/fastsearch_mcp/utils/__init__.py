"""
Utilities for FastSearch MCP.

This module provides various utility functions following FastMCP 2.12 patterns.
"""

from .file_utils import find_files, search_in_file, get_file_info, is_binary_file

__all__ = [
    "find_files",
    "search_in_file", 
    "get_file_info",
    "is_binary_file",
]
