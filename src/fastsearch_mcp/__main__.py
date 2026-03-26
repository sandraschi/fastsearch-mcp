#!/usr/bin/env python3
"""
FastSearch MCP Server - Main entry point.

This module provides the main entry point for the FastSearch MCP server,
following FastMCP 2.13 patterns and conventions.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path


def _setup_path() -> None:
    """Setup Python path for development."""
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _setup_encoding() -> None:
    """Setup encoding for Windows console compatibility."""
    if sys.platform == "win32":
        os.environ["PYTHONIOENCODING"] = "ascii:replace"


# Setup before imports
_setup_encoding()
_setup_path()

# Now imports are at top level
from fastsearch_mcp import __version__
from fastsearch_mcp.logging_config import setup_logging, struct_message
from fastsearch_mcp.server import server
from .transport import run_server_async

# Setup logging before creating logger
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main async entry point."""
    logger.info(struct_message("Starting FastSearch MCP server", version=__version__))

    try:
        # Run the server
        await run_server_async(server, server_name="fastsearch-mcp")

    except KeyboardInterrupt:
        # Server was interrupted - this is normal
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.exception(struct_message("Server error", error=str(e), error_type=type(e).__name__))
        # Also print to stderr for Claude Desktop logs
        print(f"[ERROR] Server error: {e}", file=sys.stderr)
        raise


def cli_main() -> None:
    """CLI entry point (sync). Runs async main so Cursor/uvx can start the server."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(struct_message("Fatal error", error=str(e), error_type=type(e).__name__))
        print(f"[ERROR] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
