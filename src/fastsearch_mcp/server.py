"""
FastSearch MCP Server - FastMCP 2.12 compliant implementation.

This module provides the main FastSearch MCP server implementation using FastMCP 2.12.
It follows the proper FastMCP patterns and conventions.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .logging_config import get_logger

logger = logging.getLogger(__name__)


class FastSearchServer:
    """FastSearch MCP Server using FastMCP 2.12."""
    
    def __init__(self, name: str = "fastsearch-mcp"):
        """Initialize the FastSearch MCP server."""
        self.name = name
        self.app = FastMCP(name=name)
        self._setup_tools()
    
    def _setup_tools(self) -> None:
        """Register all available tools with the FastMCP app."""
        from fastmcp.tools import Tool
        from .service_client import is_service_running
        
        # Check if C++ service is running
        service_running = is_service_running()
        if not service_running:
            logger.warning("FastSearch C++ service is not running. Tools will use fallback implementation.")
        
        # Create file search tool that uses C++ service
        file_search_tool = Tool(
            key="file_search",
            name="file_search",
            title="File Search",
            description="Search for files using direct NTFS MFT access via C++ service",
            parameters={
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (glob or regex)"
                },
                "directory": {
                    "type": "string", 
                    "description": "Directory to search in",
                    "default": "."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 100
                }
            }
        )
        
        # Create service status tool
        status_tool = Tool(
            key="service_status",
            name="service_status",
            title="Service Status",
            description="Get the status of the FastSearch C++ service",
            parameters={}
        )
        
        # Create help tool
        help_tool = Tool(
            key="help",
            name="help", 
            title="Help",
            description="Get help for available tools",
            parameters={
                "tool_name": {
                    "type": "string",
                    "description": "Name of tool to get help for (optional)",
                    "default": None
                }
            }
        )
        
        try:
            self.app.add_tool(file_search_tool)
            self.app.add_tool(status_tool)
            self.app.add_tool(help_tool)
            logger.info("Registered FastMCP 2.12 tools: file_search, service_status, help")
        except Exception as e:
            logger.error(f"Failed to register tools: {e}")
    
    async def start(self, transport: str = "stdio") -> None:
        """Start the FastSearch MCP server."""
        logger.info(f"Starting FastSearch MCP server ({self.name})")
        
        try:
            if transport == "stdio":
                await self.app.run_stdio_async()
            elif transport == "http":
                await self.app.run_http_async()
            elif transport == "sse":
                await self.app.run_sse_async()
            else:
                raise ValueError(f"Unsupported transport: {transport}")
                
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            raise
    
    def run(self, transport: str = "stdio") -> None:
        """Run the server (blocking)."""
        try:
            asyncio.run(self.start(transport))
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)


def main() -> None:
    """Main entry point for the FastSearch MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )
    
    server = FastSearchServer()
    server.run()


if __name__ == "__main__":
    main()