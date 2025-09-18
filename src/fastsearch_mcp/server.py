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
        from .service_client import is_service_running
        from .tools import AVAILABLE_TOOLS
        
        # Check if C++ service is running
        service_running = is_service_running()
        if not service_running:
            logger.warning("FastSearch C++ service is not running. Tools will use fallback implementation.")
        
        # Register all tools from the tools directory
        registered_count = 0
        for tool_class in AVAILABLE_TOOLS:
            try:
                # Get the tool definition
                tool_def = tool_class.get_definition()
                
                # Create tool instance
                tool_instance = tool_class()
                
                # Import tool wrappers
                from .tool_wrappers import TOOL_WRAPPERS
                
                # Get the appropriate wrapper for this tool
                wrapper_creator = TOOL_WRAPPERS.get(tool_def.name)
                if wrapper_creator:
                    wrapper_func = wrapper_creator(tool_instance)
                else:
                    # Fallback for unknown tools
                    async def fallback_wrapper():
                        """Fallback wrapper for unknown tools"""
                        return await tool_instance.execute()
                    wrapper_func = fallback_wrapper
                
                # Register the wrapper function with FastMCP 2.12
                self.app.tool(
                    name=tool_def.name,
                    description=tool_def.description,
                    tags={tool_def.category.value.lower().replace(" ", "_")},
                    enabled=True
                )(wrapper_func)
                
                registered_count += 1
                logger.info(f"Registered tool: {tool_def.name}")
                
            except Exception as e:
                logger.error(f"Failed to register tool {tool_class.__name__}: {e}")
        
        logger.info(f"Successfully registered {registered_count} tools from tools directory")
    
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
    
    def get_app(self) -> FastMCP:
        """Get the FastMCP app instance."""
        return self.app
    
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