"""
FastSearch MCP Server - FastMCP 3.x NTFS search service.

FastMCP 3.1 compliant: supports sampling (client-side LLM), agentic workflows,
and unified gateway (run as proxy via fastsearch_mcp.gateway). Includes direct
NTFS Master File Table access, real-time search, and filesystem analysis tools.

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
__version__ = "0.5.0"

# Ensure src is in Python path for development
if __name__ == "__main__":
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

# FastMCP 3.x imports
try:
    from fastmcp import FastMCP
except ImportError as e:
    raise ImportError("FastMCP 3.x is required. Install with: pip install 'fastmcp>=3.0.0,<4'") from e

# Local imports - import server to register tools
from .server import server

# Public API
__all__ = [
    # FastMCP class
    "FastMCP",
    # Version
    "__version__",
    # Server instance
    "server",
]
