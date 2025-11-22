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


@pytest.fixture(autouse=True)
def mock_windows_apis():
    """Auto-use fixture that mocks Windows API calls for all tests.
    
    This ensures tests can run in GitHub Actions even if Windows APIs aren't available.
    """
    # Configure the error class for pywintypes.error (needed before patching)
    class MockWinError(Exception):
        def __init__(self, winerror=None, *args, **kwargs):
            self.winerror = winerror
            self.funcname = kwargs.get("funcname", "")
            self.strerror = kwargs.get("strerror", "")

    # Create mock modules - these will be used both in sys.modules and for module patches
    # This ensures imports inside functions (like in is_service_running()) work correctly
    mock_win32file_module = MagicMock()
    mock_pywintypes_module = MagicMock()
    mock_pywintypes_module.error = MockWinError
    mock_win32pipe_module = MagicMock()
    mock_win32service_module = MagicMock()
    mock_win32serviceutil_module = MagicMock()
    mock_win32security_module = MagicMock()
    
    # Configure the mock pipe handle
    mock_handle = MagicMock()
    
    # Configure win32file mock (used by both sys.modules and module patches)
    mock_win32file_module.CreateFile.return_value = mock_handle
    mock_win32file_module.CloseHandle.return_value = None
    mock_win32file_module.FlushFileBuffers.return_value = None
    mock_win32file_module.GENERIC_READ = 0x80000000
    mock_win32file_module.GENERIC_WRITE = 0x40000000
    mock_win32file_module.OPEN_EXISTING = 3
    
    # Configure win32pipe mock
    mock_win32pipe_module.SetNamedPipeHandleState.return_value = None
    
    # Configure win32serviceutil mock
    mock_service_handle = MagicMock()
    mock_service_handle.QueryServiceConfig.return_value = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
    mock_win32serviceutil_module.OpenService.return_value = mock_service_handle
    mock_win32serviceutil_module.QueryServiceStatus.return_value = (1, 0, 0, 0, 0, 0, 0)  # Running state
    mock_win32serviceutil_module.EnumServicesStatus.return_value = [
        ("FastSearchService", "FastSearch MCP Service", 1),
    ]
    mock_win32serviceutil_module.StartService.return_value = None
    mock_win32serviceutil_module.ControlService.return_value = (1, 0, 0, 0, 0, 0, 0)
    mock_win32serviceutil_module.ChangeServiceConfig.return_value = None
    
    # Configure win32security mock
    mock_win32security_module.GetFileSecurity.return_value = MagicMock()
    
    # Mock win32file, win32pipe, pywintypes for pipe_client
    # Also patch sys.modules to catch imports inside functions
    with patch.dict(sys.modules, {
        "win32file": mock_win32file_module,
        "pywintypes": mock_pywintypes_module,
        "win32pipe": mock_win32pipe_module,
        "win32service": mock_win32service_module,
        "win32serviceutil": mock_win32serviceutil_module,
        "win32security": mock_win32security_module,
    }), \
         patch("fastsearch_mcp.pipe_client.win32file", mock_win32file_module, create=True) as mock_win32file, \
         patch("fastsearch_mcp.pipe_client.win32pipe", mock_win32pipe_module, create=True) as mock_win32pipe, \
         patch("fastsearch_mcp.pipe_client.pywintypes", mock_pywintypes_module, create=True) as mock_pywintypes, \
         patch("fastsearch_mcp.pipe_client.WINDOWS_AVAILABLE", True), \
         patch("fastsearch_mcp.service_client.win32file", mock_win32file_module, create=True) as mock_win32file_svc, \
         patch("fastsearch_mcp.service_client.pywintypes", mock_pywintypes_module, create=True) as mock_pywintypes_svc, \
         patch("fastsearch_mcp.service_client.subprocess", create=True) as mock_subprocess, \
         patch("fastsearch_mcp.tools.service.win32service", mock_win32service_module, create=True) as mock_win32service, \
         patch("fastsearch_mcp.tools.service.win32serviceutil", mock_win32serviceutil_module, create=True) as mock_win32serviceutil, \
         patch("fastsearch_mcp.tools.service_manager.win32service", mock_win32service_module, create=True) as mock_win32service_mgr, \
         patch("fastsearch_mcp.tools.service_manager.win32serviceutil", mock_win32serviceutil_module, create=True) as mock_win32serviceutil_mgr, \
         patch("fastsearch_mcp.tools.ntfs.win32file", mock_win32file_module, create=True) as mock_win32file_ntfs, \
         patch("fastsearch_mcp.tools.ntfs.win32security", mock_win32security_module, create=True) as mock_win32security:
        
        # Configure ReadFile and WriteFile to use test data
        test_response = json.dumps({"status": "ok", "results": []}).encode("utf-8")
        response_length = len(test_response).to_bytes(4, "little")
        
        mock_win32file_module.ReadFile.side_effect = [
            (0, response_length),  # Length prefix
            (0, test_response),  # Actual response data
        ]

        # Configure WriteFile to return the number of bytes written
        mock_win32file_module.WriteFile.return_value = (0, len(response_length) + len(test_response))

        # Configure ReadFile and WriteFile to use test data
        test_response = json.dumps({"status": "ok", "results": []}).encode("utf-8")
        response_length = len(test_response).to_bytes(4, "little")
        
        # Configure ReadFile for pipe operations
        mock_win32file_module.ReadFile.side_effect = [
            (0, response_length),  # Length prefix
            (0, test_response),  # Actual response data
        ]

        # Configure WriteFile to return the number of bytes written
        mock_win32file_module.WriteFile.return_value = (0, len(response_length) + len(test_response))

        # Mock subprocess.run for is_service_running() fallback
        # Default: service is running (process found)
        mock_subprocess_result = MagicMock()
        mock_subprocess_result.stdout = "FastSearchServiceNew.exe"
        mock_subprocess_result.returncode = 0
        mock_subprocess.run.return_value = mock_subprocess_result

        # Mock NTFS functions (using the same mock_win32file_module)
        mock_win32file_module.GetFileAttributesW.return_value = 32  # Normal file

        yield {
            "win32file": mock_win32file_module,
            "win32pipe": mock_win32pipe_module,
            "pywintypes": mock_pywintypes_module,
            "win32file_svc": mock_win32file_module,
            "subprocess": mock_subprocess,
            "win32service": mock_win32service_module,
            "win32serviceutil": mock_win32serviceutil_module,
            "win32service_mgr": mock_win32service_module,
            "win32serviceutil_mgr": mock_win32serviceutil_module,
            "win32file_ntfs": mock_win32file_module,
            "win32security": mock_win32security_module,
            "handle": mock_handle,
            "service_handle": mock_service_handle,
        }


@pytest.fixture
def mock_pipe_client():
    """Fixture that provides a mocked NamedPipeClient."""
    from fastsearch_mcp.pipe_client import NamedPipeClient
    
    with patch.object(NamedPipeClient, 'connect', new_callable=AsyncMock) as mock_connect, \
         patch.object(NamedPipeClient, 'disconnect', new_callable=AsyncMock) as mock_disconnect, \
         patch.object(NamedPipeClient, 'send_request', new_callable=AsyncMock) as mock_send:
        
        mock_connect.return_value = True
        mock_send.return_value = {"status": "ok", "results": []}
        
        client = NamedPipeClient(pipe_name=TEST_PIPE_NAME)
        client.connect = mock_connect
        client.disconnect = mock_disconnect
        client.send_request = mock_send
        
        yield client


@pytest.fixture
def server():
    """Fixture that provides an McpServer instance with a test pipe name."""
    from fastsearch_mcp.mcp_server import McpServer

    return McpServer(service_pipe=TEST_PIPE_NAME)


@pytest.fixture
def mock_service_client():
    """Fixture that mocks service_client functions."""
    with patch("fastsearch_mcp.service_client.is_service_running", return_value=True), \
         patch("fastsearch_mcp.service_client.get_service_status", new_callable=AsyncMock) as mock_status, \
         patch("fastsearch_mcp.service_client.search_files", new_callable=AsyncMock) as mock_search, \
         patch("fastsearch_mcp.service_client.test_service_connection", new_callable=AsyncMock) as mock_test:
        
        mock_status.return_value = {
            "running": True,
            "service_state": "running",
            "executable_path": "C:\\Program Files\\FastSearch\\FastSearchServiceNew.exe",
        }
        mock_search.return_value = [
            {"path": "C:\\test\\file1.txt", "size": 1024, "attributes": 32},
            {"path": "C:\\test\\file2.txt", "size": 2048, "attributes": 32},
        ]
        mock_test.return_value = True
        
        yield {
            "status": mock_status,
            "search": mock_search,
            "test": mock_test,
        }


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
    with patch("fastsearch_mcp.service_client.search_files", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = test_search_results
        yield test_search_results
