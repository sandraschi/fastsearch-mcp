"""Integration tests for FastSearch MCP Bridge."""

import asyncio
import unittest
from typing import Dict, Any

from fastsearch_mcp.mcp_server import McpServer


class TestMcpBridge(unittest.IsolatedAsyncioTestCase):
    """Test cases for the MCP bridge."""

    async def asyncSetUp(self):
        """Set up test environment."""
        self.server = McpServer()

    async def test_get_capabilities(self):
        """Test that the server reports its capabilities correctly."""
        result = await self.server.get_capabilities()
        self.assertIn("fastsearch", result)
        self.assertIn("version", result["fastsearch"])

    async def test_search(self):
        """Test search functionality."""
        result = await self.server.handle_search(query="*.py", search_type="glob")
        self.assertIn("results", result)
        self.assertIn("total", result)
        self.assertIsInstance(result["results"], list)


class TestMcpBridgeIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for the MCP bridge with the actual service."""
    
    @unittest.SkipTest
    async def test_end_to_end_search(self):
        """Test end-to-end search functionality with the real service."""
        # This would require the actual service to be running
        # and is marked as an integration test
        pass


if __name__ == "__main__":
    import pytest
    import sys
    
    # Run unit tests by default
    if len(sys.argv) > 1 and sys.argv[1] == "--integration":
        # Run integration tests
        sys.exit(pytest.main([__file__, "-m", "integration"]))
    else:
        # Run unit tests
        sys.exit(pytest.main([__file__]))
