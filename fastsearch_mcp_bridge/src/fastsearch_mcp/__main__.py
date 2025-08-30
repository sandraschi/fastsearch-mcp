"""Main entry point for the FastSearch MCP bridge."""

import argparse
import asyncio
import logging
import os
import signal
import sys
from typing import Optional

from . import __version__
from .mcp_server import McpServer


def parse_args(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="FastSearch MCP Bridge")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version and exit",
    )
    parser.add_argument(
        "--service-pipe",
        default=os.getenv("FASTSEARCH_PIPE", r"\\.\pipe\fastsearch-service"),
        help="Path to FastSearch service pipe (default: %(default)s)",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: %(default)s)",
    )
    return parser.parse_args(args)


async def async_main(args: argparse.Namespace):
    """Async entry point for the MCP server."""
    logger = logging.getLogger("fastsearch_mcp")
    
    # Set up signal handlers
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        signame = signal.Signals(signum).name
        logger.info(f"Received signal {signame}, shutting down...")
        shutdown_event.set()
    
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler, sig)
    
    # Create and start the MCP server
    server = McpServer(service_pipe=args.service_pipe)
    
    try:
        # Start the server in a task
        server_task = asyncio.create_task(server.start())
        
        # Wait for shutdown signal or server task completion
        done, pending = await asyncio.wait(
            [shutdown_event.wait(), server_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # If we're here because of the shutdown event, cancel the server task
        if not server_task.done():
            logger.info("Shutting down server...")
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
    
    except asyncio.CancelledError:
        logger.info("Server task was cancelled")
        return 0
    except Exception as e:
        logger.exception("Fatal error in MCP server")
        return 1
    finally:
        # Clean up signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.remove_signal_handler(sig)
            except Exception as e:
                logger.debug(f"Error removing signal handler for {sig}: {e}")
    
    logger.info("MCP server shutdown complete")
    return 0


def main(args: Optional[argparse.Namespace] = None):
    """Main entry point."""
    if args is None:
        args = parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("fastsearch_mcp")
    
    try:
        # Get the current event loop (FastMCP's loop)
        loop = asyncio.get_event_loop()
        
        # Run the async main function in the existing loop
        return loop.run_until_complete(async_main(args))
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested, exiting...")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main(parse_args()))
