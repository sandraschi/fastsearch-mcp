"""
Tests for the McpServer class.

These tests verify the functionality of the MCP server implementation.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the package root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'fastsearch_mcp_bridge' / 'src'))

from fastsearch_mcp import McpServer, __version__
from fastsearch_mcp.ipc import IpcError, FastSearchClient

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_mcp_server.log')
    ]
)
logger = logging.getLogger('test_mcp_server')

# Test configuration
TEST_PIPE_NAME = r"\\.\pipe\fastsearch-test"

@pytest.fixture
def mock_client():
    """Fixture that provides a mock FastSearchClient."""
    with patch('fastsearch_mcp.mcp_server.FastSearchClient') as mock:
        # Configure the mock client
        client = AsyncMock()
        client.get_status.return_value = {
            'status': 'running',
            'version': '1.0.0',
            'indexed_files': 1000,
            'index_size_mb': 10.5,
            'last_indexed': '2023-01-01T00:00:00Z'
        }
        client.search.return_value = [
            {'path': 'C:\\test\\file1.txt', 'size': 1024},
            {'path': 'C:\\test\\file2.txt', 'size': 2048}
        ]
        mock.return_value.__aenter__.return_value = client
        yield client

@pytest.fixture
def server():
    """Fixture that provides an McpServer instance with a test pipe name."""
    return McpServer(service_pipe=TEST_PIPE_NAME)

@pytest.mark.asyncio
async def test_server_initialization(server):
    """Test that the server initializes correctly."""
    assert server is not None
    assert hasattr(server, 'start')
    assert hasattr(server, 'close')
    assert server.service_pipe == TEST_PIPE_NAME

@pytest.mark.asyncio
async def test_start_server(server, mock_client):
    """Test starting the server and handling a simple request."""
    # Create a task to run the server
    server_task = asyncio.create_task(server.start())
    
    try:
        # Give the server a moment to start
        await asyncio.sleep(0.1)
        
        # Create a client and connect to the server
        client = FastSearchClient(pipe_name=TEST_PIPE_NAME)
        await client.connect()
        
        try:
            # Test a status request
            status = await client.get_status()
            assert isinstance(status, dict)
            assert 'status' in status
            assert 'version' in status
            
            # Test a search request
            results = await client.search("test", max_results=2)
            assert isinstance(results, list)
            
        finally:
            # Clean up
            await client.disconnect()
            
    finally:
        # Stop the server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

@pytest.mark.asyncio
async def test_handle_get_capabilities(server):
    """Test the get_capabilities handler."""
    # Call the handler directly
    capabilities = await server.handle_get_capabilities()
    
    # Check the response structure
    assert isinstance(capabilities, dict)
    assert 'name' in capabilities
    assert 'version' in capabilities
    assert 'tools' in capabilities
    assert isinstance(capabilities['tools'], list)
    
    # Check that expected tools are registered
    tool_names = [tool['name'] for tool in capabilities['tools']]
    assert 'mcp.get_capabilities' in tool_names
    assert 'mcp.ping' in tool_names
    assert 'mcp.shutdown' in tool_names
    assert 'fastsearch.search' in tool_names
    assert 'fastsearch.status' in tool_names

@pytest.mark.asyncio
async def test_handle_ping(server):
    """Test the ping handler."""
    response = await server.handle_ping()
    assert response == "pong"

@pytest.mark.asyncio
async def test_handle_shutdown(server):
    """Test the shutdown handler."""
    # The shutdown handler should set the shutdown event
    assert not server._shutdown_event.is_set()
    response = await server.handle_shutdown()
    assert server._shutdown_event.is_set()
    assert response == "shutting down"

@pytest.mark.asyncio
async def test_handle_search(server, mock_client):
    """Test the search handler."""
    # Test with a simple query
    results = await server.handle_search("test", max_results=2)
    
    # Check the response structure
    assert isinstance(results, list)
    assert len(results) == 2
    assert all(isinstance(item, dict) for item in results)
    
    # Verify the mock was called correctly
    mock_client.search.assert_called_once_with(
        pattern="test",
        search_type="fuzzy",
        max_results=2,
        **{}
    )

@pytest.mark.asyncio
async def test_handle_status(server, mock_client):
    """Test the status handler."""
    status = await server.handle_status()
    
    # Check the response structure
    assert isinstance(status, dict)
    assert 'service' in status
    assert 'status' in status
    assert 'version' in status
    assert 'indexed_files' in status
    assert 'index_size_mb' in status
    assert 'last_indexed' in status
    
    # Verify the mock was called
    mock_client.get_status.assert_called_once()

@pytest.mark.asyncio
async def test_register_tool(server):
    """Test registering a new tool."""
    # Define a test tool
    async def test_tool(arg1: str, arg2: int = 42):
        """Test tool documentation."""
        return {"arg1": arg1, "arg2": arg2}
    
    # Register the tool
    server.register_tool("test.tool", test_tool)
    
    # Check that the tool was registered
    assert "test.tool" in server._tool_registry
    
    # Call the tool through the server
    result = await server._execute_handler({
        "jsonrpc": "2.0",
        "method": "test.tool",
        "params": {"arg1": "test", "arg2": 123},
        "id": 1
    })
    
    # Check the response
    assert result == {"arg1": "test", "arg2": 123}

@pytest.mark.asyncio
async def test_invalid_jsonrpc_version(server):
    """Test handling of invalid JSON-RPC version."""
    with pytest.raises(ValueError) as excinfo:
        await server._process_single_request({
            "jsonrpc": "1.0",  # Invalid version
            "method": "mcp.ping",
            "id": 1
        })
    assert "Unsupported JSON-RPC version" in str(excinfo.value)

@pytest.mark.asyncio
async def test_method_not_found(server):
    """Test handling of unknown methods."""
    with pytest.raises(LookupError) as excinfo:
        await server._process_single_request({
            "jsonrpc": "2.0",
            "method": "nonexistent.method",
            "id": 1
        })
    assert "Method not found" in str(excinfo.value)
