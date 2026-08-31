#!/usr/bin/env python3
"""
Start the FastSearch MCP server for testing.

This script starts the FastSearch MCP server with default settings
and keeps it running until interrupted.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add the package root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "fastsearch_mcp_bridge" / "src"))

from fastsearch_mcp import McpServer, __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("server.log")],
)
logger = logging.getLogger("fastsearch_mcp")


async def main():
    """Start the MCP server and keep it running."""
    logger.info(f"Starting FastSearch MCP Server v{__version__}")

    # Create and start the server
    server = McpServer(service_pipe="\\.\\pipe\\fastsearch-test")
    server_task = asyncio.create_task(server.start())

    # Set up signal handlers for graceful shutdown
    stop_event = asyncio.Event()

    def signal_handler(signum, frame):
        signame = signal.Signals(signum).name
        logger.info(f"Received signal {signame}, shutting down...")
        stop_event.set()

    # Register signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler, sig)
            logger.debug(f"Registered signal handler for {sig.name}")
        except (NotImplementedError, RuntimeError) as e:
            logger.warning(f"Could not register signal handler for {sig.name}: {e}")

    try:
        # Wait for shutdown signal
        logger.info("Server is running. Press Ctrl+C to stop.")
        await stop_event.wait()

    except asyncio.CancelledError:
        logger.info("Server task was cancelled")

    finally:
        # Clean up
        logger.info("Shutting down server...")
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

        # Close the server
        if hasattr(server, "close"):
            await server.close()

        logger.info("Server shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested, exiting...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
