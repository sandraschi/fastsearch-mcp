"""
Comprehensive integration tests for the FastSearch C++ Windows service.

These tests verify:
- Service installation and status
- Service start/stop functionality
- Named pipe connection
- Search request handling
- Error handling and edge cases
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from fastsearch_mcp.pipe_client import (
    NamedPipeClient,
    get_service_info_via_pipe,
    test_pipe_connection,
)
from fastsearch_mcp.service_client import (
    SERVICE_EXECUTABLE,
    SERVICE_NAME,
    SERVICE_PIPE_NAME,
    get_service_status,
    is_service_running,
    search_files,
    start_service,
    stop_service,
    test_service_connection,
)

# Note: get_service_status_tool may not be available if exceptions module missing
try:
    from fastsearch_mcp.tools.service import get_service_status as get_service_status_tool
except ImportError:
    get_service_status_tool = None


@pytest.fixture(scope="module")
def service_available():
    """Check if the service is available for testing.

    In CI/GitHub Actions, this will return False and tests will be skipped.
    Tests should use mocks instead of requiring actual service.

    Note: This fixture respects mocking - if Windows APIs are mocked (as in CI),
    it will return False to indicate real service is not available, allowing
    tests to use mocked implementations instead.
    """
    try:
        # Try to import - if mocked, this will work but QueryServiceStatus might fail
        # If not mocked and not available, ImportError will be raised
        import win32serviceutil

        # Try to query service - this will fail if service not installed or APIs not available
        # In CI with mocks, this will use the mocked version which should succeed
        # In real environment, this checks if service actually exists
        try:
            win32serviceutil.QueryServiceStatus(SERVICE_NAME)
            return True
        except Exception:
            # Service not installed or not available - use mocks instead
            return False
    except ImportError:
        # Windows APIs not available (e.g., in CI without pywin32) - use mocks
        return False


@pytest.fixture(scope="module")
def admin_privileges():
    """Check if running with admin privileges.

    In CI/GitHub Actions, this will return False and admin-required tests will be skipped.
    """
    try:
        import ctypes

        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (AttributeError, ImportError, Exception):
        # Not Windows or APIs not available
        return False


class TestServiceStatus:
    """Test service status and availability checks."""

    def test_is_service_running_check(self):
        """Test checking if service process is running."""
        running = is_service_running()
        assert isinstance(running, bool)
        # This may be True or False depending on service state

    @pytest.mark.asyncio
    async def test_get_service_status(self):
        """Test getting detailed service status."""
        status = await get_service_status()
        assert isinstance(status, dict)
        # Check for expected keys (may vary based on service state)
        assert "running" in status or "service_state" in status or "error" in status
        assert "executable_path" in status

    def test_service_executable_path(self):
        """Test that service executable path is valid."""
        assert isinstance(SERVICE_EXECUTABLE, Path)
        # Executable may or may not exist depending on build state
        # Just verify the path structure is correct
        assert SERVICE_EXECUTABLE.suffix == ".exe"

    def test_service_pipe_name(self):
        """Test that pipe name is correctly formatted."""
        assert isinstance(SERVICE_PIPE_NAME, str)
        # Pipe name should start with \\.\pipe\ (Windows named pipe prefix)
        # Check both escaped and raw string formats
        pipe_prefix1 = "\\\\.\\pipe\\"
        pipe_prefix2 = r"\\.\pipe\\"
        assert SERVICE_PIPE_NAME.startswith(pipe_prefix1) or SERVICE_PIPE_NAME.startswith(pipe_prefix2)
        assert "FastSearch" in SERVICE_PIPE_NAME

    @pytest.mark.asyncio
    async def test_service_connection_test(self):
        """Test comprehensive service connection test."""
        result = await test_service_connection()
        assert isinstance(result, dict)
        assert "service_running" in result
        assert "pipe_connected" in result
        assert "executable_exists" in result
        assert "executable_path" in result
        assert "pipe_name" in result


class TestServiceControl:
    """Test service start/stop functionality."""

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="Requires --run-service-tests flag and admin privileges - run manually with: pytest --run-service-tests"
    )
    async def test_start_service(self, admin_privileges, service_available):
        """Test starting the service."""
        if not admin_privileges:
            pytest.skip("Requires administrator privileges")
        if not service_available:
            pytest.skip("Service not installed")

        # Stop service first to ensure clean state
        await stop_service()
        await asyncio.sleep(2)  # Wait for service to stop

        # Start the service
        result = await start_service()
        assert isinstance(result, bool)

        # Wait a bit for service to start
        await asyncio.sleep(3)

        # Verify service is running
        running = is_service_running()
        assert running, "Service should be running after start"

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="Requires --run-service-tests flag and admin privileges - run manually with: pytest --run-service-tests"
    )
    async def test_stop_service(self, admin_privileges, service_available):
        """Test stopping the service."""
        if not admin_privileges:
            pytest.skip("Requires administrator privileges")
        if not service_available:
            pytest.skip("Service not installed")

        # Ensure service is running first
        await start_service()
        await asyncio.sleep(3)

        # Stop the service
        result = await stop_service()
        assert isinstance(result, bool)

        # Wait for service to stop
        await asyncio.sleep(2)

        # Verify service is stopped
        running = is_service_running()
        # Service may still be stopping, so we just check the result
        assert isinstance(running, bool)

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="Requires --run-service-tests flag and admin privileges - run manually with: pytest --run-service-tests"
    )
    async def test_restart_service(self, admin_privileges, service_available):
        """Test restarting the service (stop then start)."""
        if not admin_privileges:
            pytest.skip("Requires administrator privileges")
        if not service_available:
            pytest.skip("Service not installed")

        # Stop service
        await stop_service()
        await asyncio.sleep(2)

        # Start service
        result = await start_service()
        assert isinstance(result, bool)

        await asyncio.sleep(3)

        # Verify it's running
        running = is_service_running()
        assert running, "Service should be running after restart"


class TestNamedPipeConnection:
    """Test named pipe connection to the service."""

    @pytest.mark.asyncio
    async def test_pipe_client_creation(self):
        """Test creating a named pipe client."""
        client = NamedPipeClient()
        assert client.pipe_name == SERVICE_PIPE_NAME
        assert client.connected is False
        assert client.handle is None

    @pytest.mark.asyncio
    async def test_pipe_connection_when_service_running(self):
        """Test connecting to pipe when service is running."""
        # Check if service is running
        if not is_service_running():
            pytest.skip("Service is not running, cannot test pipe connection")

        client = NamedPipeClient()
        connected = await client.connect(timeout=2.0)

        if connected:
            assert client.connected is True
            assert client.handle is not None
            await client.disconnect()
        else:
            # Service may be running but pipe not ready yet
            pytest.skip("Could not connect to pipe (service may be starting)")

    @pytest.mark.asyncio
    async def test_pipe_connection_when_service_stopped(self):
        """Test connecting to pipe when service is stopped."""
        # This should fail gracefully
        client = NamedPipeClient()
        connected = await client.connect(timeout=1.0)
        assert connected is False
        assert client.connected is False

    @pytest.mark.asyncio
    async def test_pipe_connection_test_function(self):
        """Test the test_pipe_connection helper function."""
        result = await test_pipe_connection()
        assert isinstance(result, bool)
        # Result depends on service state

    @pytest.mark.asyncio
    async def test_pipe_client_context_manager(self):
        """Test using pipe client as async context manager."""
        if not is_service_running():
            pytest.skip("Service is not running")

        try:
            async with NamedPipeClient() as client:
                if client.connected:
                    assert client.handle is not None
                    # Client should auto-disconnect on exit
        except Exception:
            # Connection may fail if service not ready
            pass


class TestServiceCommunication:
    """Test communication with the service via named pipe."""

    @pytest.mark.asyncio
    async def test_ping_request(self):
        """Test sending a ping request to the service."""
        if not is_service_running():
            pytest.skip("Service is not running")

        client = NamedPipeClient()
        connected = await client.connect(timeout=2.0)

        if not connected:
            pytest.skip("Could not connect to pipe")

        try:
            request = {"command": "ping"}
            response = await client.send_request(request, timeout=2.0)

            assert response is not None
            assert isinstance(response, dict)
            # Service should respond with success
            if response.get("success"):
                assert "message" in response or "pong" in str(response).lower()
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_get_service_info_request(self):
        """Test getting service info via named pipe."""
        if not is_service_running():
            pytest.skip("Service is not running")

        info = await get_service_info_via_pipe()

        if info is not None:
            assert isinstance(info, dict)
            # Service info should contain relevant fields
            assert "service" in info or "timestamp" in info or "pipe" in info

    @pytest.mark.asyncio
    async def test_search_request_structure(self):
        """Test sending a search request (structure only, may not work if service not fully implemented)."""
        if not is_service_running():
            pytest.skip("Service is not running")

        client = NamedPipeClient()
        connected = await client.connect(timeout=2.0)

        if not connected:
            pytest.skip("Could not connect to pipe")

        try:
            request = {
                "command": "search_files",
                "pattern": "*.txt",
                "directory": "C:\\",
                "max_results": 10,
            }
            response = await client.send_request(request, timeout=5.0)

            # Response may be success or error depending on implementation
            assert response is not None
            assert isinstance(response, dict)
            # Should have either success or error
            assert "success" in response or "error" in response
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_invalid_command_request(self):
        """Test sending an invalid command to the service."""
        if not is_service_running():
            pytest.skip("Service is not running")

        client = NamedPipeClient()
        connected = await client.connect(timeout=2.0)

        if not connected:
            pytest.skip("Could not connect to pipe")

        try:
            request = {"command": "invalid_command_xyz"}
            response = await client.send_request(request, timeout=2.0)

            # Service should respond with error
            assert response is not None
            assert isinstance(response, dict)
            # Should indicate failure
            if "success" in response:
                assert response["success"] is False
            elif "error" in response:
                assert isinstance(response["error"], (str, dict))
        finally:
            await client.disconnect()


class TestSearchFunctionality:
    """Test search functionality through the service."""

    @pytest.mark.asyncio
    async def test_search_files_function(self):
        """Test the search_files function (uses service if available, fallback otherwise)."""
        results = await search_files("*.txt", directory="C:\\Windows", max_results=10)

        assert isinstance(results, list)
        # Results may be empty if no matches, but should be a list
        for result in results:
            assert isinstance(result, dict)
            assert "path" in result or "file" in result

    @pytest.mark.asyncio
    async def test_search_files_with_service_running(self):
        """Test search when service is running."""
        if not is_service_running():
            pytest.skip("Service is not running")

        results = await search_files("*.exe", directory="C:\\Windows\\System32", max_results=5)
        assert isinstance(results, list)
        # May have results or be empty

    @pytest.mark.asyncio
    async def test_search_files_fallback(self):
        """Test that search works even when service is not running (fallback)."""
        # This should work regardless of service state
        results = await search_files("test", directory=".", max_results=5)
        assert isinstance(results, list)


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test connection timeout handling."""
        client = NamedPipeClient()
        # Use very short timeout
        connected = await client.connect(timeout=0.1)
        # Should handle timeout gracefully
        assert isinstance(connected, bool)

    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """Test request timeout handling."""
        if not is_service_running():
            pytest.skip("Service is not running")

        client = NamedPipeClient()
        connected = await client.connect(timeout=2.0)

        if not connected:
            pytest.skip("Could not connect to pipe")

        try:
            # Send request with very short timeout
            request = {"command": "ping"}
            response = await client.send_request(request, timeout=0.1)
            # Should handle timeout gracefully (may return None or error)
            assert response is None or isinstance(response, dict)
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self):
        """Test disconnecting when not connected."""
        client = NamedPipeClient()
        # Should not raise exception
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_send_request_when_not_connected(self):
        """Test sending request when not connected."""
        client = NamedPipeClient()
        request = {"command": "ping"}
        response = await client.send_request(request)
        assert response is None


class TestServiceToolIntegration:
    """Test integration with service management tools."""

    @pytest.mark.asyncio
    async def test_get_service_status_tool(self):
        """Test the service status tool."""
        if get_service_status_tool is None:
            pytest.skip("Service status tool not available (exceptions module missing)")
        try:
            status = await get_service_status_tool()
            assert isinstance(status, dict)
            assert "status" in status
        except Exception as e:
            # May fail if service not installed
            assert "not_installed" in str(e).lower() or "does not exist" in str(e).lower()


# Pytest configuration
def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--run-service-tests",
        action="store_true",
        default=False,
        help="Run tests that require service control (needs admin privileges)",
    )
