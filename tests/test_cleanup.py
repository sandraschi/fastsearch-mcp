"""
Tests for resource cleanup in FastSearch MCP server and client.

These tests verify that all resources are properly cleaned up when the server or client is closed.
"""

import asyncio
import gc
import logging
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
import pywintypes
import win32file
import win32pipe

# Add the package root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'fastsearch_mcp_bridge' / 'src'))

from fastsearch_mcp.mcp_server import McpServer
from fastsearch_mcp.ipc import FastSearchClient, IpcError, IpcConnectionError

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_cleanup.log')
    ]
)
logger = logging.getLogger('test_cleanup')

# Test configuration
TEST_PIPE_NAME = r"\\.\pipe\fastsearch-test-cleanup"

@pytest.fixture
def mock_win32():
    """Fixture that mocks the Windows API calls."""
    with patch('fastsearch_mcp.ipc.win32file') as mock_win32file, \
         patch('fastsearch_mcp.ipc.win32pipe') as mock_win32pipe, \
         patch('fastsearch_mcp.ipc.pywintypes') as mock_pywintypes:
        
        # Configure the mock pipe handle
        mock_handle = MagicMock()
        
        # Configure CreateFile to return our mock handle
        mock_win32file.CreateFile.return_value = mock_handle
        
        # Configure ReadFile and WriteFile to use test data
        test_response = json.dumps({"status": "ok"}).encode('utf-8')
        mock_win32file.ReadFile.side_effect = [
            (0, len(test_response).to_bytes(4, 'little')),  # Length prefix
            (0, test_response)  # Actual response data
        ]
        
        # Configure WriteFile to return the number of bytes written
        mock_win32file.WriteFile.return_value = (0, 8)  # 4 bytes length + 4 bytes data
        
        # Configure SetNamedPipeHandleState to succeed
        mock_win32pipe.SetNamedPipeHandleState.return_value = None
        
        # Configure FlushFileBuffers to succeed
        mock_win32file.FlushFileBuffers.return_value = None
        
        # Configure CloseHandle to succeed
        mock_win32file.CloseHandle.return_value = None
        
        # Configure the error class for pywintypes.error
        class MockWinError(Exception):
            def __init__(self, winerror=None, *args, **kwargs):
                self.winerror = winerror
                self.funcname = kwargs.get('funcname', '')
                self.strerror = kwargs.get('strerror', '')
                
        mock_pywintypes.error = MockWinError
        
        yield {
            'win32file': mock_win32file,
            'win32pipe': mock_win32pipe,
            'pywintypes': mock_pywintypes,
            'handle': mock_handle
        }

@pytest.mark.asyncio
async def test_mcp_server_cleanup():
    """Test that McpServer cleans up resources properly when closed."""
    # Create a server instance
    server = McpServer(service_pipe=TEST_PIPE_NAME)
    
    # Mock the client to avoid actual connections
    mock_client = AsyncMock()
    mock_client.disconnect = AsyncMock()
    server._client = mock_client
    
    # Start the server
    server._running = True
    
    # Close the server
    await server.close()
    
    # Verify that the client was closed
    mock_client.disconnect.assert_awaited_once()
    
    # Verify server state is cleaned up
    assert not server._running
    assert server._shutdown_event.is_set()
    assert server._client is None

@pytest.mark.asyncio
async def test_mcp_server_cleanup_with_exception():
    """Test that McpServer handles exceptions during cleanup."""
    # Create a server instance
    server = McpServer(service_pipe=TEST_PIPE_NAME)
    
    # Mock the client to raise an exception during disconnect
    mock_client = AsyncMock()
    mock_client.disconnect = AsyncMock(side_effect=Exception("Test exception"))
    server._client = mock_client
    
    # Start the server
    server._running = True
    
    # Close the server - should not raise
    await server.close()
    
    # Verify that the client's disconnect was called
    mock_client.disconnect.assert_awaited_once()
    
    # Verify server state is still cleaned up
    assert not server._running
    assert server._shutdown_event.is_set()
    assert server._client is None

@pytest.mark.asyncio
async def test_fastsearch_client_cleanup():
    """Test that FastSearchClient cleans up resources properly when closed."""
    # Create a client instance
    client = FastSearchClient(pipe_name=TEST_PIPE_NAME)
    
    # Mock the Windows API calls
    with patch('win32file.CreateFile') as mock_create_file, \
         patch('win32pipe.SetNamedPipeHandleState') as mock_set_pipe_state, \
         patch('win32file.CloseHandle') as mock_close_handle:
        
        # Configure mocks
        mock_handle = MagicMock()
        mock_create_file.return_value = mock_handle
        
        # Connect the client
        await client.connect()
        
        # Verify the client is connected
        assert client.connected
        assert client.pipe_handle is not None
        
        # Close the client
        await client.close()
        
        # Verify the client is disconnected
        assert not client.connected
        assert client.pipe_handle is None
        
        # Verify CloseHandle was called
        mock_close_handle.assert_called_once_with(mock_handle)

@pytest.mark.asyncio
async def test_fastsearch_client_cleanup_with_exception():
    """Test that FastSearchClient handles exceptions during cleanup."""
    # Create a client instance
    client = FastSearchClient(pipe_name=TEST_PIPE_NAME)
    
    # Mock the Windows API calls
    with patch('win32file.CreateFile') as mock_create_file, \
         patch('win32pipe.SetNamedPipeHandleState') as mock_set_pipe_state, \
         patch('win32file.CloseHandle') as mock_close_handle:
        
        # Configure mocks
        mock_handle = MagicMock()
        mock_create_file.return_value = mock_handle
        mock_close_handle.side_effect = Exception("Test exception")
        
        # Connect the client
        await client.connect()
        
        # Close the client - should not raise
        await client.close()
        
        # Verify CloseHandle was called
        mock_close_handle.assert_called_once_with(mock_handle)
        
        # Verify client state is still cleaned up
        assert not client.connected
        assert client.pipe_handle is None

@pytest.mark.asyncio
async def test_fastsearch_client_context_manager():
    """Test that FastSearchClient cleans up resources when used as a context manager."""
    # Mock the Windows API calls
    with patch('win32file.CreateFile') as mock_create_file, \
         patch('win32pipe.SetNamedPipeHandleState') as mock_set_pipe_state, \
         patch('win32file.CloseHandle') as mock_close_handle:
        
        # Configure mocks
        mock_handle = MagicMock()
        mock_create_file.return_value = mock_handle
        
        # Use the client as a context manager
        async with FastSearchClient(pipe_name=TEST_PIPE_NAME) as client:
            # Verify the client is connected
            assert client.connected
            assert client.pipe_handle is not None
        
        # Verify the client is disconnected after the context manager exits
        assert not client.connected
        assert client.pipe_handle is None
        
        # Verify CloseHandle was called
        mock_close_handle.assert_called_once_with(mock_handle)

@pytest.mark.asyncio
async def test_fastsearch_client_garbage_collection():
    """Test that FastSearchClient cleans up resources during garbage collection."""
    # Mock the Windows API calls
    with patch('win32file.CreateFile') as mock_create_file, \
         patch('win32pipe.SetNamedPipeHandleState') as mock_set_pipe_state, \
         patch('win32file.CloseHandle') as mock_close_handle:
        
        # Configure mocks
        mock_handle = MagicMock()
        mock_create_file.return_value = mock_handle
        
        # Create a client and connect it
        client = FastSearchClient(pipe_name=TEST_PIPE_NAME)
        await client.connect()
        
        # Store the handle for verification
        pipe_handle = client.pipe_handle
        
        # Delete the client and force garbage collection
        del client
        gc.collect()
        
        # Give the garbage collector some time to run
        await asyncio.sleep(0.1)
        
        # Verify CloseHandle was called on the pipe handle
        mock_close_handle.assert_called_once_with(pipe_handle)

@pytest.mark.asyncio
async def test_mcp_server_context_manager():
    """Test that McpServer cleans up resources when used as a context manager."""
    # Create a mock client
    mock_client = AsyncMock()
    mock_client.disconnect = AsyncMock()
    
    # Patch the FastSearchClient to return our mock
    with patch('fastsearch_mcp.mcp_server.FastSearchClient') as mock_client_class:
        mock_client_class.return_value = mock_client
        
        # Use the server as a context manager
        async with McpServer(service_pipe=TEST_PIPE_NAME) as server:
            # Verify the server is running
            assert server._running
            
            # Verify the client was created
            mock_client_class.assert_called_once_with(pipe_name=TEST_PIPE_NAME)
            
            # Verify the client was connected
            mock_client.connect.assert_awaited_once()
        
        # Verify the client was disconnected
        mock_client.disconnect.assert_awaited_once()
        
        # Verify server state is cleaned up
        assert not server._running
        assert server._shutdown_event.is_set()
        assert server._client is None
