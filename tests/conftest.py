"""
Pytest configuration and fixtures for FastSearch MCP tests.
"""

import asyncio
import json
import logging
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import McpError

# Add project root to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_PIPE_NAME = r"\\.\pipe\fastsearch-test"

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("test.log")],
)
logger = logging.getLogger("conftest")

# Create test data directory if it doesn't exist
TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    # Clean up
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create and clean up a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="fastsearch_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_data_dir() -> Path:
    """Return path to test data directory."""
    return TEST_DATA_DIR


@pytest.fixture
def mock_mcp_error():
    """Fixture to test McpError handling."""

    class MockMcpError(McpError):
        def __init__(self, message="Test error", code=-32000, data=None):
            super().__init__(message=message, code=code, data=data)

    return MockMcpError


@pytest.fixture
def mock_win32():
    """Fixture that mocks the Windows API calls."""
    with patch("fastsearch_mcp.ipc.win32file") as mock_win32file, patch(
        "fastsearch_mcp.ipc.win32pipe"
    ) as mock_win32pipe, patch("fastsearch_mcp.ipc.pywintypes") as mock_pywintypes:
        # Configure the mock pipe handle
        mock_handle = MagicMock()

        # Configure CreateFile to return our mock handle
        mock_win32file.CreateFile.return_value = mock_handle

        # Configure ReadFile and WriteFile to use test data
        test_response = json.dumps({"status": "ok"}).encode("utf-8")
        mock_win32file.ReadFile.side_effect = [
            (0, len(test_response).to_bytes(4, "little")),  # Length prefix
            (0, test_response),  # Actual response data
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
                self.funcname = kwargs.get("funcname", "")
                self.strerror = kwargs.get("strerror", "")

        mock_pywintypes.error = MockWinError

        yield {
            "win32file": mock_win32file,
            "win32pipe": mock_win32pipe,
            "pywintypes": mock_pywintypes,
            "handle": mock_handle,
        }


@pytest.fixture
def client():
    """Fixture that provides a FastSearchClient instance with a test pipe name."""
    from fastsearch_mcp.ipc import FastSearchClient

    return FastSearchClient(pipe_name=TEST_PIPE_NAME)


@pytest.fixture
def server():
    """Fixture that provides an McpServer instance with a test pipe name."""
    from fastsearch_mcp.mcp_server import McpServer

    return McpServer(service_pipe=TEST_PIPE_NAME)


@pytest.fixture
def mock_client():
    """Fixture that provides a mock FastSearchClient."""
    with patch("fastsearch_mcp.mcp_server.FastSearchClient") as mock:
        # Configure the mock client
        client = AsyncMock()
        client.get_status.return_value = {
            "status": "running",
            "version": "1.0.0",
            "indexed_files": 1000,
            "index_size_mb": 10.5,
            "last_indexed": "2023-01-01T00:00:00Z",
        }
        client.search.return_value = [
            {"path": "C:\\test\\file1.txt", "size": 1024},
            {"path": "C:\\test\\file2.txt", "size": 2048},
        ]
        mock.return_value.__aenter__.return_value = client
        yield client


@pytest.fixture
def test_files(temp_dir: Path) -> List[Path]:
    """Create test files in a temporary directory."""
    files = []

    # Create some test files
    for i in range(5):
        file_path = temp_dir / f"test_file_{i}.txt"
        file_path.write_text(f"This is test file {i}")
        files.append(file_path)

    # Create a subdirectory with more files
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    for i in range(3):
        file_path = subdir / f"subfile_{i}.txt"
        file_path.write_text(f"This is subfile {i}")
        files.append(file_path)

    return files


@pytest.fixture
def test_search_results() -> List[Dict[str, Any]]:
    """Return sample search results for testing."""
    return [
        {
            "path": "C:\\test\\file1.txt",
            "size": 1024,
            "modified": "2023-01-01T00:00:00Z",
            "attributes": 32,
        },
        {
            "path": "C:\\test\\file2.txt",
            "size": 2048,
            "modified": "2023-01-02T00:00:00Z",
            "attributes": 32,
        },
        {
            "path": "C:\\test\\document.pdf",
            "size": 1048576,
            "modified": "2023-01-03T00:00:00Z",
            "attributes": 32,
        },
        {
            "path": "C:\\test\\image.jpg",
            "size": 524288,
            "modified": "2023-01-04T00:00:00Z",
            "attributes": 32,
        },
        {
            "path": "C:\\test\\archive.zip",
            "size": 10485760,
            "modified": "2023-01-05T00:00:00Z",
            "attributes": 32,
        },
    ]


@pytest.fixture
def mock_search_results(test_search_results: List[Dict[str, Any]]):
    """Fixture that mocks search results."""
    with patch("fastsearch_mcp.mcp_server.FastSearchClient") as mock:
        client = AsyncMock()
        client.search.return_value = test_search_results
        mock.return_value.__aenter__.return_value = client
        yield test_search_results
