""
FastSearch MCP - Command Line Interface

This module provides the entry point for the DXT package.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional

from .mcp_server import McpServer
from .decorators import generate_markdown_docs

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

async def run_server() -> None:
    """Run the MCP server."""
    server = McpServer()
    await server.start()

def generate_docs() -> None:
    """Generate documentation for the MCP API."""
    from fastsearch_mcp import mcp_server
    generate_markdown_docs(mcp_server, "docs/api.md")
    print("Documentation generated at docs/api.md")

def print_help() -> None:
    """Print help message."""
    print("""FastSearch MCP - Fast file search for Claude Desktop

Usage:
  fastsearch-mcp run     Run the MCP server (default)
  fastsearch-mcp docs    Generate API documentation
  fastsearch-mcp help    Show this help message
""")

def main() -> None:
    """Main entry point for the CLI."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "docs":
            generate_docs()
            return
        elif command in ("-h", "--help", "help"):
            print_help()
            return
    
    # Default action: run the server
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
