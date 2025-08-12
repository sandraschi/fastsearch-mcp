"""FastMCP 2.10 server with decorator-based documentation.

This module implements the MCP server that communicates with the FastSearch Windows service
via named pipes for performing high-performance NTFS searches.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, List

from .decorators import mcp_method
from .pipe_client import PipeClient, PipeClientError

logger = logging.getLogger(__name__)

class McpServer:
    """MCP server with decorator-based documentation."""
    
    def __init__(self, pipe_name: str = r"\\.\pipe\fastsearch-service"):
        """Initialize the MCP server.
        
        Args:
            pipe_name: Name of the named pipe to connect to the FastSearch service.
        """
        self.pipe_client = PipeClient(pipe_name)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.pipe_client.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.pipe_client.close()
    
    @mcp_method(
        name="fastsearch.search",
        description="Search files using direct MFT access.",
        params={
            "query": {"type": "string", "required": True},
            "search_type": {
                "type": "string", 
                "default": "glob",
                "enum": ["glob", "regex", "exact", "fuzzy"],
                "description": "Type of search to perform. One of: glob, regex, exact, fuzzy"
            },
            "limit": {
                "type": "integer",
                "default": 100,
                "minimum": 1,
                "maximum": 1000,
                "description": "Maximum number of results to return"
            },
            "include": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["*"],
                "description": "File patterns to include (e.g., ['*.txt', '*.pdf'])"
            },
            "exclude": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "description": "File patterns to exclude"
            },
            "case_sensitive": {
                "type": "boolean",
                "default": False,
                "description": "Whether the search is case-sensitive"
            },
            "path": {
                "type": "string",
                "default": "C:\\",
                "description": "Root path to search within"
            }
        },
        returns={
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "size": {"type": "integer"},
                            "modified": {"type": "string", "format": "date-time"},
                            "created": {"type": "string", "format": "date-time"},
                            "is_dir": {"type": "boolean"}
                        }
                    }
                },
                "total": {"type": "integer"},
                "stats": {
                    "type": "object",
                    "properties": {
                        "scanned_files": {"type": "integer"},
                        "matched_files": {"type": "integer"},
                        "search_time_ms": {"type": "number"}
                    }
                }
            },
            "required": ["results", "total", "stats"]
        }
    )
    async def handle_search(
        self,
        query: str,
        search_type: str = "glob",
        limit: int = 100,
        include: List[str] = None,
        exclude: List[str] = None,
        case_sensitive: bool = False,
        path: str = "C:\\"
    ) -> Dict[str, Any]:
        """Search for files using the FastSearch service.
        
        Args:
            query: The search query (pattern, regex, or exact text)
            search_type: Type of search (glob, regex, exact, fuzzy)
            limit: Maximum number of results to return
            include: List of file patterns to include
            exclude: List of file patterns to exclude
            case_sensitive: Whether the search is case-sensitive
            path: Root path to search within
            
        Returns:
            Dict containing search results and statistics
        """
        params = {
            "query": query,
            "search_type": search_type,
            "limit": limit,
            "include": include or ["*"],
            "exclude": exclude or [],
            "case_sensitive": case_sensitive,
            "path": path
        }
        
        try:
            # Forward the search request to the Windows service
            result = await self.pipe_client.send_request("search", params)
            return {
                "results": result.get("results", []),
                "total": result.get("total", 0),
                "stats": result.get("stats", {})
            }
        except PipeClientError as e:
            logger.error(f"Search failed: {e}")
            return {
                "results": [],
                "total": 0,
                "stats": {
                    "error": str(e),
                    "scanned_files": 0,
                    "matched_files": 0,
                    "search_time_ms": 0
                }
            }

    @mcp_method(
        name="mcp.get_capabilities",
        description="Get server capabilities.",
        returns={
            "type": "object",
            "properties": {
                "fastsearch": {
                    "type": "object",
                    "properties": {
                        "version": {"type": "string"},
                        "features": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "search_types": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["version", "features", "search_types"]
                }
            },
            "required": ["fastsearch"]
        }
    )
    async def get_capabilities(self) -> Dict[str, Any]:
        """Return capabilities of the FastSearch service."""
        try:
            # Try to get capabilities from the service
            service_capabilities = await self.pipe_client.send_request("get_capabilities")
            return {"fastsearch": service_capabilities}
        except PipeClientError as e:
            logger.warning(f"Could not get service capabilities: {e}")
            # Return default capabilities if service is not available
            return {
                "fastsearch": {
                    "version": "1.0.0",
                    "features": ["search", "stats"],
                    "search_types": ["glob", "regex", "exact", "fuzzy"]
                }
            }
