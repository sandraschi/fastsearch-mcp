"""Direct WizTree MFT search tool for MCP."""

import logging
from typing import Any

from fastsearch_mcp.mcp_instance import mcp
from fastsearch_mcp.wiztree_bridge import is_wiztree_available, search_files_wiztree

logger = logging.getLogger(__name__)


@mcp.tool(
    name="wiztree_mft_search",
    description="Lightning-fast NTFS MFT file search across local drives using Antibody Software's WizTree engine. Requires no background daemon.",
)
async def wiztree_mft_search(
    pattern: str,
    path: str = "*",
    search_all: bool = False,
    max_results: int = 500,
) -> dict[str, Any]:
    """Search for files instantly using the WizTree MFT engine.

    Args:
        pattern: File name or wildcard pattern (e.g. '*.py', '*Foster*', 'README.md')
        path: Drive letter or path (e.g. 'C:\\', 'E:\\', or '*' for all drives)
        search_all: If True, search all connected NTFS drives
        max_results: Maximum results to return (default: 500)

    Returns:
        Dictionary with success, count, and results list with file path, size, and modification date.
    """
    if not is_wiztree_available():
        return {
            "success": False,
            "error": "WizTree executable not found on system. Ensure WizTree is installed in Program Files.",
            "results": [],
            "count": 0,
        }

    try:
        return await search_files_wiztree(
            pattern=pattern,
            directory=path,
            max_results=max_results,
            search_all=search_all,
        )
    except Exception as e:
        logger.error(f"WizTree MFT search error: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "count": 0,
        }
