"""
FastSearch MCP Server - FastMCP 2.13 compliant NTFS search service.

This package provides a FastMCP 2.13 compliant implementation of the Model Context Protocol (MCP)
for the FastSearch NTFS search service. It includes direct NTFS Master File Table access,
real-time search capabilities, and various filesystem analysis tools.

Architecture:
- Direct NTFS MFT access (no indexing/caching)
- Real-time search results
- Sub-100ms search performance
- Minimal memory footprint (<50MB)
- Instant startup (<1s)

Key Features:
- Pattern-based file search
- Disk analysis and monitoring
- Duplicate file detection
- File integrity checking
- System resource monitoring
- Service management tools
"""

import sys
from pathlib import Path

# Package version
__version__ = "0.4.0"

# Ensure src is in Python path for development
if __name__ == "__main__":
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

# FastMCP 2.13 imports
try:
    from fastmcp import FastMCP
except ImportError as e:
    raise ImportError(
        "FastMCP 2.13 is required but not installed. Install with: pip install fastmcp>=2.13.0"
    ) from e

# Local imports
from .server import FastSearchServer
from .tools import (
    DiskAnalyzerTool,
    DuplicateFileFinderTool,
    FileContentSearchTool,
    FileIntegrityCheckerTool,
    GetServiceLogsTool,
    GetServiceTool,
    ListServicesTool,
    RestartServiceTool,
    SetServiceStartupTypeTool,
    StartServiceTool,
    StopServiceTool,
    SystemResourceMonitorTool,
)

# Public API
__all__ = [
    # Core classes
    "FastSearchServer",
    "FastMCP",
    # Tools
    "FileContentSearchTool",
    "DiskAnalyzerTool",
    "DuplicateFileFinderTool",
    "FileIntegrityCheckerTool",
    "SystemResourceMonitorTool",
    "ListServicesTool",
    "GetServiceTool",
    "StartServiceTool",
    "StopServiceTool",
    "RestartServiceTool",
    "SetServiceStartupTypeTool",
    "GetServiceLogsTool",
    # Version
    "__version__",
]


# Create default server instance
def create_server() -> FastSearchServer:
    """Create a new FastSearch MCP server instance."""
    return FastSearchServer()


# Main entry point
def main() -> None:
    """Main entry point for the FastSearch MCP server."""
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
