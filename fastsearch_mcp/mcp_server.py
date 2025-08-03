"""FastMCP 2.10 server with decorator-based documentation."""

import asyncio
from typing import Any, Dict, Optional
from .decorators import mcp_method

class McpServer:
    """MCP server with decorator-based documentation."""
    
    @mcp_method(
        name="fastsearch.search",
        description="Search files using direct MFT access.",
        params={
            "query": {"type": "string", "required": True},
            "search_type": {"type": "string", "default": "glob"}
        },
        returns={"type": "object"}
    )
    async def handle_search(self, query: str, search_type: str = "glob") -> Dict[str, Any]:
        """Search implementation."""
        return {"results": [], "total": 0}

    @mcp_method(
        name="mcp.get_capabilities",
        description="Get server capabilities.",
        returns={"type": "object"}
    )
    async def get_capabilities(self) -> Dict[str, Any]:
        """Return capabilities."""
        return {"fastsearch": {"version": "1.0.0"}}
