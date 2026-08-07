#!/usr/bin/env python3
"""
Test script for FastSearch MCP server.

This script verifies that the FastSearch MCP server starts correctly,
handles basic operations, and cleans up resources properly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the package root to the Python path
sys.path.insert(0, str(Path(__file__).parent / "fastsearch_mcp_bridge" / "src"))

from fastsearch_mcp.ipc import FastSearchClient, IpcError

from fastsearch_mcp import McpServer, __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("test_fastsearch.log")],
)
logger = logging.getLogger("test_fastsearch")


class FastSearchTester:
    """Test harness for FastSearch MCP server."""

    def __init__(self):
        """Initialize the test harness."""
        self.server = None
        self.server_task = None
        self.shutdown_event = asyncio.Event()
        self.pipe_name = r"\\.\pipe\fastsearch-test"

    async def start_server(self):
        """Start the MCP server in a background task."""
        logger.info("Starting MCP server...")
        self.server = McpServer(service_pipe=self.pipe_name)
        self.server_task = asyncio.create_task(self.server.start())

        # Give the server a moment to start
        await asyncio.sleep(1)
        logger.info("MCP server started")

    async def stop_server(self):
        """Stop the MCP server."""
        if self.server_task and not self.server_task.done():
            logger.info("Stopping MCP server...")
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
            logger.info("MCP server stopped")

    async def test_connection(self):
        """Test basic connection to the server."""
        logger.info("Testing connection to server...")

        try:
            async with FastSearchClient(pipe_name=self.pipe_name) as client:
                # Test a simple status request
                status = await client.get_status()
                logger.info(f"Server status: {status}")
                return True

        except IpcError as e:
            logger.error(f"Connection test failed: {e}")
            return False
        except Exception:
            logger.exception("Unexpected error during connection test")
            return False

    async def test_search(self):
        """Test search functionality."""
        logger.info("Testing search functionality...")

        try:
            async with FastSearchClient(pipe_name=self.pipe_name) as client:
                # Test a simple search
                results = await client.search(pattern="test", search_type="fuzzy", max_results=5)

                logger.info(f"Search results: {results}")
                return True

        except IpcError as e:
            logger.error(f"Search test failed: {e}")
            return False
        except Exception:
            logger.exception("Unexpected error during search test")
            return False

    async def run_tests(self):
        """Run all tests."""
        logger.info(f"Starting FastSearch MCP tests (v{__version__})")

        try:
            # Start the server
            await self.start_server()

            # Run tests
            tests = [("Connection Test", self.test_connection), ("Search Test", self.test_search)]

            all_passed = True
            for name, test_func in tests:
                logger.info(f"\n=== {name} ===")
                try:
                    success = await test_func()
                    status = "PASSED" if success else "FAILED"
                    logger.info(f"{name}: {status}")
                    all_passed = all_passed and success
                except Exception as e:
                    logger.error(f"Error during {name}: {e}", exc_info=True)
                    all_passed = False

            return all_passed

        except Exception as e:
            logger.error(f"Test harness error: {e}", exc_info=True)
            return False

        finally:
            # Ensure the server is stopped
            await self.stop_server()
            logger.info("Test harness shutdown complete")


def main():
    """Main entry point for the test script."""
    # Set up signal handlers
    loop = asyncio.get_event_loop()
    tester = FastSearchTester()

    # Run the tests
    success = loop.run_until_complete(tester.run_tests())

    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
