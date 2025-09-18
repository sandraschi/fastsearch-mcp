"""
Integration tests for the MCP server.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastmcp.exceptions import McpError
from fastsearch_mcp.mcp_server import McpServer, JsonRpcRequest, JsonRpcResponse

class TestMcpServerIntegration:
    """Integration tests for the McpServer class."""
    
    @pytest.fixture
    async def mcp_server(self):
        ""Create an McpServer instance for testing."""
        server = McpServer()
        yield server
        if hasattr(server, '_client') and server._client:
            await server._client.close()
    
    @pytest.mark.asyncio
    async def test_handle_ping(self, mcp_server):
        ""Test the ping handler returns 'pong'."""
        response = await mcp_server.handle_ping()
        assert response == "pong"
    
    @pytest.mark.asyncio
    async def test_handle_get_capabilities(self, mcp_server):
        ""Test the get_capabilities handler returns expected structure."""
        capabilities = await mcp_server.handle_get_capabilities()
        assert 'version' in capabilities
        assert 'tools' in capabilities
        assert isinstance(capabilities['tools'], list)
    
    @pytest.mark.asyncio
    async def test_process_valid_request(self, mcp_server):
        ""Test processing a valid JSON-RPC request."""
        request = {
            "jsonrpc": "2.0",
            "method": "mcp.ping",
            "id": 1
        }
        response = await mcp_server._process_single_request(request)
        assert response['jsonrpc'] == '2.0'
        assert response['result'] == 'pong'
        assert response['id'] == 1
    
    @pytest.mark.asyncio
    async def test_process_invalid_method(self, mcp_server):
        ""Test processing a request with an invalid method."""
        request = {
            "jsonrpc": "2.0",
            "method": "nonexistent.method",
            "id": 1
        }
        response = await mcp_server._process_single_request(request)
        assert response['jsonrpc'] == '2.0'
        assert 'error' in response
        assert response['error']['code'] == -32601  # Method not found
        assert response['id'] == 1

    @pytest.mark.asyncio
    async def test_process_invalid_json(self, mcp_server):
        ""Test processing invalid JSON."""
        with pytest.raises(ValueError):
            await mcp_server._process_request("invalid json")
    
    @pytest.mark.asyncio
    async def test_handle_search_invalid_params(self, mcp_server):
        ""Test search with invalid parameters."""
        with pytest.raises(ValueError):
            await mcp_server.handle_search("", search_type="invalid_type")
