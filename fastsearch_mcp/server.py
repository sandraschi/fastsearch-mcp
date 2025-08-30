"""FastSearch MCP Server entry point.

This module provides the standard MCP server interface for the FastSearch service.
It acts as a bridge between the MCP protocol and the internal server implementation.
"""

import asyncio
import logging
import sys

from .mcp_server import McpServer

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the FastSearch MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )
    
    async def run_server():
        """Run the MCP server with proper stdio handling."""
        server = McpServer()
        try:
            await server.start(stdin=sys.stdin, stdout=sys.stdout)
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            raise
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
