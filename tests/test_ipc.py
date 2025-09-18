"""
Tests for the IPC (Inter-Process Communication) module.

These tests verify the functionality of the FastSearch IPC client and related utilities.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
import pywintypes
import win32file
import win32pipe

# Add the package root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'fastsearch_mcp_bridge' / 'src'))

from fastsearch_mcp.ipc import (
    FastSearchClient,
    IpcError,
    IpcConnectionError,
    IpcTimeoutError,
    IpcProtocolError,
    MSG_SEARCH,
    MSG_STATUS
)

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_ipc.log')
    ]
)
logger = logging.getLogger('test_ipc')

# Test configuration
TEST_PIPE_NAME = r"\\.\pipe\fastsearch-test-ipc"
TEST_MESSAGE = b"test message"
TEST_RESPONSE = b"test response"

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
        
        # Configure ReadFile and WriteFile to use our test data
        mock_win32file.ReadFile.side_effect = [
            (0, len(TEST_RESPONSE).to_bytes(4, 'little')),  # Length prefix
            (0, TEST_RESPONSE)  # Actual response data
        ]
        
        # Configure WriteFile to return the number of bytes written
        mock_win32file.WriteFile.return_value = (0, len(TEST_MESSAGE) + 4)  # +4 for length prefix
        
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

@pytest.fixture
def client():
    """Fixture that provides a FastSearchClient instance with a test pipe name."""
    return FastSearchClient(pipe_name=TEST_PIPE_NAME)

@pytest.mark.asyncio
async def test_connect_success(client, mock_win32):
    """Test successful connection to the named pipe."""
    # Test connection
    await client.connect()
    
    # Verify the connection was established
    assert client.connected
    assert client.pipe_handle is not None
    
    # Verify the Windows API was called correctly
    mock_win32['win32file'].CreateFile.assert_called_once()
    mock_win32['win32pipe'].SetNamedPipeHandleState.assert_called_once()

@pytest.mark.asyncio
async def test_connect_pipe_not_found(client, mock_win32):
    """Test connection failure when the named pipe doesn't exist."""
    # Configure CreateFile to raise a "file not found" error
    mock_win32['win32file'].CreateFile.side_effect = mock_win32['pywintypes'].error(
        winerror=2,  # ERROR_FILE_NOT_FOUND
        funcname='CreateFile',
        strerror='The system cannot find the file specified.'
    )
    
    # Test connection should raise IpcConnectionError
    with pytest.raises(IpcConnectionError) as excinfo:
        await client.connect()
    
    # Verify the error message
    assert "not found" in str(excinfo.value).lower()
    assert not client.connected
    assert client.pipe_handle is None

@pytest.mark.asyncio
async def test_connect_pipe_busy(client, mock_win32):
    """Test connection failure when all pipe instances are busy."""
    # Configure CreateFile to raise a "pipe busy" error
    mock_win32['win32file'].CreateFile.side_effect = mock_win32['pywintypes'].error(
        winerror=231,  # ERROR_PIPE_BUSY
        funcname='CreateFile',
        strerror='All pipe instances are busy.'
    )
    
    # Test connection should raise IpcConnectionError
    with pytest.raises(IpcConnectionError) as excinfo:
        await client.connect()
    
    # Verify the error message
    assert "busy" in str(excinfo.value).lower()
    assert not client.connected
    assert client.pipe_handle is None

@pytest.mark.asyncio
async def test_disconnect(client, mock_win32):
    """Test disconnecting from the named pipe."""
    # First connect
    await client.connect()
    assert client.connected
    
    # Then disconnect
    await client.disconnect()
    
    # Verify the connection was closed
    assert not client.connected
    assert client.pipe_handle is None
    
    # Verify CloseHandle was called
    mock_win32['win32file'].CloseHandle.assert_called_once()

@pytest.mark.asyncio
async def test_send_message_success(client, mock_win32):
    """Test sending a message successfully."""
    # Connect first
    await client.connect()
    
    # Send a test message
    response = await client._send_message(MSG_SEARCH, TEST_MESSAGE)
    
    # Verify the response
    assert response == TEST_RESPONSE
    
    # Verify the message was sent correctly
    mock_win32['win32file'].WriteFile.assert_called_once()
    
    # The first call should be the message length (4 bytes)
    args, _ = mock_win32['win32file'].WriteFile.call_args_list[0]
    assert len(args) >= 3  # At least handle, data, overlapped
    
    # The message should start with the length prefix (4 bytes)
    message = args[1]
    assert len(message) == len(TEST_MESSAGE) + 4  # +4 for length prefix
    
    # The first 4 bytes should be the length of the actual message
    message_length = int.from_bytes(message[:4], 'little')
    assert message_length == len(TEST_MESSAGE)
    
    # The rest should be the original message
    assert message[4:] == TEST_MESSAGE

@pytest.mark.asyncio
async def test_send_message_not_connected(client):
    """Test sending a message when not connected."""
    with pytest.raises(IpcError) as excinfo:
        await client._send_message(MSG_SEARCH, TEST_MESSAGE)
    
    assert "not connected" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_search(client, mock_win32):
    """Test the search method."""
    # Configure a mock response
    search_results = [
        {"path": "C:\\test\\file1.txt", "size": 1024},
        {"path": "C:\\test\\file2.txt", "size": 2048}
    ]
    
    # Update the mock to return our test response
    mock_win32['win32file'].ReadFile.side_effect = [
        (0, len(json.dumps(search_results).encode('utf-8')).to_bytes(4, 'little')),
        (0, json.dumps(search_results).encode('utf-8'))
    ]
    
    # Connect first
    await client.connect()
    
    # Perform a search
    results = await client.search(
        pattern="test",
        search_type="fuzzy",
        max_results=10,
        path="C:\\test"
    )
    
    # Verify the results
    assert results == search_results
    
    # Verify the message was sent correctly
    mock_win32['win32file'].WriteFile.assert_called_once()
    
    # The message should be a JSON-encoded search request
    _, message_args, _ = mock_win32['win32file'].WriteFile.mock_calls[0][1]
    message = json.loads(message_args[4:].decode('utf-8'))  # Skip length prefix
    
    assert message['pattern'] == "test"
    assert message['type'] == "fuzzy"
    assert message['max_results'] == 10
    assert message['filters']['path'] == "C:\\test"

@pytest.mark.asyncio
async def test_get_status(client, mock_win32):
    """Test the get_status method."""
    # Configure a mock response
    status_data = {
        'status': 'running',
        'version': '1.0.0',
        'indexed_files': 1000,
        'index_size_mb': 10.5,
        'last_indexed': '2023-01-01T00:00:00Z'
    }
    
    # Update the mock to return our test response
    mock_win32['win32file'].ReadFile.side_effect = [
        (0, len(json.dumps(status_data).encode('utf-8')).to_bytes(4, 'little')),
        (0, json.dumps(status_data).encode('utf-8'))
    ]
    
    # Connect first
    await client.connect()
    
    # Get the status
    status = await client.get_status()
    
    # Verify the status
    assert status == status_data
    
    # Verify the message was sent correctly
    mock_win32['win32file'].WriteFile.assert_called_once()
    
    # The message should be a status request
    _, message_args, _ = mock_win32['win32file'].WriteFile.mock_calls[0][1]
    message = json.loads(message_args[4:].decode('utf-8'))  # Skip length prefix
    
    assert message == {'type': 'status'}

@pytest.mark.asyncio
async def test_context_manager(client, mock_win32):
    """Test using the client as a context manager."""
    async with client:
        # Client should be connected inside the context
        assert client.connected
        assert client.pipe_handle is not None
        
        # The connect method should have been called
        mock_win32['win32file'].CreateFile.assert_called_once()
    
    # Client should be disconnected outside the context
    assert not client.connected
    assert client.pipe_handle is None
    
    # The disconnect method should have been called
    mock_win32['win32file'].CloseHandle.assert_called_once()

@pytest.mark.asyncio
async def test_double_connect(client, mock_win32):
    """Test connecting twice to the same client."""
    # First connection should work
    await client.connect()
    assert client.connected
    
    # Get the current handle
    original_handle = client.pipe_handle
    
    # Second connection should be a no-op
    await client.connect()
    assert client.connected
    assert client.pipe_handle is original_handle
    
    # Clean up
    await client.disconnect()

@pytest.mark.asyncio
async def test_double_disconnect(client, mock_win32):
    """Test disconnecting twice from the same client."""
    # First disconnect after connect
    await client.connect()
    await client.disconnect()
    assert not client.connected
    
    # Reset the mock to track the second CloseHandle call
    mock_win32['win32file'].CloseHandle.reset_mock()
    
    # Second disconnect should be a no-op
    await client.disconnect()
    assert not client.connected
    
    # CloseHandle should not have been called again
    mock_win32['win32file'].CloseHandle.assert_not_called()

@pytest.mark.asyncio
async def test_send_message_timeout(client, mock_win32):
    """Test handling of timeouts when sending a message."""
    # Configure WriteFile to simulate a timeout
    mock_win32['win32file'].WriteFile.side_effect = mock_win32['pywintypes'].error(
        winerror=258,  # WAIT_TIMEOUT
        funcname='WriteFile',
        strerror='The wait operation timed out.'
    )
    
    # Connect first
    await client.connect()
    
    # Sending a message should raise IpcTimeoutError
    with pytest.raises(IpcTimeoutError):
        await client._send_message(MSG_SEARCH, TEST_MESSAGE)

@pytest.mark.asyncio
async def test_receive_message_timeout(client, mock_win32):
    """Test handling of timeouts when receiving a message."""
    # Configure ReadFile to simulate a timeout on the first call
    mock_win32['win32file'].ReadFile.side_effect = [
        mock_win32['pywintypes'].error(
            winerror=258,  # WAIT_TIMEOUT
            funcname='ReadFile',
            strerror='The wait operation timed out.'
        ),
        (0, len(TEST_RESPONSE).to_bytes(4, 'little')),
        (0, TEST_RESPONSE)
    ]
    
    # Connect first
    await client.connect()
    
    # Sending a message should still work despite the initial timeout
    response = await client._send_message(MSG_SEARCH, TEST_MESSAGE)
    assert response == TEST_RESPONSE

@pytest.mark.asyncio
async def test_invalid_message_format(client, mock_win32):
    """Test handling of invalid message formats."""
    # Configure ReadFile to return an invalid message (too short for length prefix)
    mock_win32['win32file'].ReadFile.return_value = (0, b'123')  # Only 3 bytes, need 4
    
    # Connect first
    await client.connect()
    
    # Sending a message should raise IpcProtocolError
    with pytest.raises(IpcProtocolError) as excinfo:
        await client._send_message(MSG_SEARCH, TEST_MESSAGE)
    
    assert "invalid message format" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_connection_reset(client, mock_win32):
    """Test handling of connection reset by peer."""
    # Configure WriteFile to simulate a broken pipe
    mock_win32['win32file'].WriteFile.side_effect = mock_win32['pywintypes'].error(
        winerror=232,  # ERROR_NO_DATA (simulating broken pipe)
        funcname='WriteFile',
        strerror='The pipe is being closed.'
    )
    
    # Connect first
    await client.connect()
    
    # Sending a message should raise IpcConnectionError
    with pytest.raises(IpcConnectionError) as excinfo:
        await client._send_message(MSG_SEARCH, TEST_MESSAGE)
    
    assert "connection lost" in str(excinfo.value).lower()
    
    # Client should be marked as disconnected
    assert not client.connected
    assert client.pipe_handle is None
