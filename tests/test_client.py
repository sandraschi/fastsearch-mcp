"""
Tests for the FastSearchClient class.

These tests verify the basic functionality of the FastSearch IPC client.
"""

import logging
import sys
from pathlib import Path

import pytest

# Add the package root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "fastsearch_mcp_bridge" / "src"))

from fastsearch_mcp.ipc import FastSearchClient, IpcConnectionError, IpcError

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("test_client.log")],
)
logger = logging.getLogger("test_client")

# Test configuration
TEST_PIPE_NAME = r"\\.\pipe\fastsearch-test"


@pytest.fixture
def client():
    """Fixture that provides a FastSearchClient instance."""
    return FastSearchClient(pipe_name=TEST_PIPE_NAME)


@pytest.mark.asyncio
async def test_connect_disconnect(client):
    """Test connecting to and disconnecting from the server."""
    try:
        # Test connection
        await client.connect()
        assert client.connected, "Client should be connected after connect()"

        # Test disconnection
        await client.disconnect()
        assert not client.connected, "Client should be disconnected after disconnect()"

    except IpcError as e:
        pytest.fail(f"Connection test failed: {e}")
    finally:
        # Ensure cleanup
        if client.connected:
            await client.disconnect()


@pytest.mark.asyncio
async def test_context_manager(client):
    """Test using the client as an async context manager."""
    try:
        async with client:
            assert client.connected, "Client should be connected inside context manager"

        assert not client.connected, "Client should be disconnected after context manager"

    except IpcError as e:
        pytest.fail(f"Context manager test failed: {e}")


@pytest.mark.asyncio
async def test_get_status(client):
    """Test getting server status."""
    try:
        async with client:
            status = await client.get_status()

            # Check that status has the expected structure
            assert isinstance(status, dict), "Status should be a dictionary"
            assert "status" in status, "Status should contain 'status' field"
            assert "version" in status, "Status should contain 'version' field"

    except IpcError as e:
        pytest.fail(f"Status test failed: {e}")


@pytest.mark.asyncio
async def test_search(client):
    """Test performing a search."""
    try:
        async with client:
            # Test a simple search
            results = await client.search(pattern="test", search_type="fuzzy", max_results=5)

            # Check that results have the expected structure
            assert isinstance(results, list), "Results should be a list"

    except IpcError as e:
        pytest.fail(f"Search test failed: {e}")


@pytest.mark.asyncio
async def test_invalid_pipe():
    """Test connecting to a non-existent pipe."""
    invalid_client = FastSearchClient(pipe_name=r"\\.\pipe\nonexistent-pipe-12345")

    with pytest.raises(IpcConnectionError):
        await invalid_client.connect()

    assert not invalid_client.connected, "Client should not be connected after failed connection"


@pytest.mark.asyncio
async def test_double_connect(client):
    """Test connecting twice to the same client."""
    try:
        # First connection should work
        await client.connect()
        assert client.connected

        # Second connection should be a no-op
        await client.connect()
        assert client.connected

    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_double_disconnect(client):
    """Test disconnecting twice from the same client."""
    # First disconnect after connect
    await client.connect()
    await client.disconnect()
    assert not client.connected

    # Second disconnect should be a no-op
    await client.disconnect()
    assert not client.connected
