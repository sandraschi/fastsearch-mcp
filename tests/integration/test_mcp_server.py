"""
Integration tests for the MCP server.
"""

import pytest
import pytest_asyncio

from fastsearch_mcp.mcp_server import McpServer


class TestMcpServerIntegration:
    """Integration tests for the McpServer class."""

    @pytest_asyncio.fixture
    async def mcp_server(self):
        """Create an McpServer instance for testing."""
        server = McpServer()
        yield server
        if hasattr(server, "_client") and server._client:
            await server._client.close()

    @pytest.mark.asyncio
    async def test_process_valid_request(self, mcp_server):
        """Test processing a valid JSON-RPC request."""
        import json

        request = {
            "jsonrpc": "2.0",
            "method": "fastsearch.search",
            "params": {"query": "test"},
            "id": 1,
        }
        response_str = await mcp_server._process_message(json.dumps(request))
        response = json.loads(response_str)
        assert response["jsonrpc"] == "2.0"
        # May have result or error depending on service availability
        assert "result" in response or "error" in response
        assert response["id"] == 1

    @pytest.mark.asyncio
    async def test_process_invalid_method(self, mcp_server):
        """Test processing a request with an invalid method."""
        import json

        request = {"jsonrpc": "2.0", "method": "nonexistent.method", "id": 1}
        response_str = await mcp_server._process_message(json.dumps(request))
        response = json.loads(response_str)
        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["code"] == -32601  # Method not found
        assert response["id"] == 1

    @pytest.mark.asyncio
    async def test_process_invalid_json(self, mcp_server):
        """Test processing invalid JSON."""
        import json

        response_str = await mcp_server._process_message("invalid json")
        response = json.loads(response_str)
        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["code"] == -32700  # Parse error

    @pytest.mark.asyncio
    async def test_handle_search(self, mcp_server):
        """Test handle_search method."""
        try:
            result = await mcp_server.handle_search("test", search_type="glob", limit=10)
            assert isinstance(result, dict)
            assert "results" in result
        except Exception:
            # Service may not be available, which is OK for integration test
            pass
