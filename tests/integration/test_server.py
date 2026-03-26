#!/usr/bin/env python3
"""
Test script for FastSearch MCP server.

This script tests the basic functionality of the FastSearch MCP server,
including starting the server, performing a search, and shutting down.
"""

import asyncio
import json
import logging
import os
import sys

# Add the package root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'fastsearch_mcp_bridge', 'src')))

from fastsearch_mcp.ipc import FastSearchClient

from fastsearch_mcp import McpServer, __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_server.log')
    ]
)
logger = logging.getLogger('test_server')

class TestServer:
    """Test harness for the FastSearch MCP server."""

    def __init__(self):
        """Initialize the test harness."""
        self.server = None
        self.server_task = None
        self.shutdown_event = asyncio.Event()

    async def start_server(self):
        """Start the MCP server in a background task."""
        logger.info("Starting MCP server...")
        self.server = McpServer(service_pipe="\\.\\pipe\\fastsearch-test")
        self.server_task = asyncio.create_task(self.server.start())
        logger.info("MCP server started")

        # Wait for the server to be ready
        await asyncio.sleep(1)

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

    async def test_search(self):
        """Test the search functionality."""
        logger.info("Testing search functionality...")

        # Create a client
        async with FastSearchClient(pipe_name="\\\\.\\pipe\\fastsearch-test") as client:
            # Test a simple search
            results = await client.search(
                pattern="test",
                search_type="fuzzy",
                max_results=10
            )

            logger.info(f"Search results: {json.dumps(results, indent=2, default=str)}")
            return True

    async def test_status(self):
        """Test the status functionality."""
        logger.info("Testing status functionality...")

        # Create a client
        async with FastSearchClient(pipe_name="\\\\.\\pipe\\fastsearch-test") as client:
            # Get status
            status = await client.get_status()

            logger.info(f"Service status: {json.dumps(status, indent=2, default=str)}")
            return True

    async def run_tests(self):
        """Run all tests."""
        logger.info("Starting FastSearch MCP server tests")
        logger.info(f"Version: {__version__}")

        try:
            # Start the server
            await self.start_server()

            # Run tests
            await self.test_status()
            await self.test_search()

            return True

        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)
            return False

        finally:
            # Ensure the server is stopped
            await self.stop_server()

def main():
    """Main entry point for the test script."""
    # Set up signal handlers
    loop = asyncio.get_event_loop()
    test_harness = TestServer()

    # Run the tests
    success = loop.run_until_complete(test_harness.run_tests())

    # Return appropriate exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
