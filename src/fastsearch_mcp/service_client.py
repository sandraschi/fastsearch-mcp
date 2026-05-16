"""
Service client for communicating with the FastSearch C++ service.

This module provides functions to communicate with the FastSearch C++ service
via named pipes for NTFS MFT access.
"""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .logging_config import get_logger
from .pipe_client import (
    get_pipe_name,
    get_service_info_via_pipe,
    search_files_via_pipe,
    test_pipe_connection,
)

logger = get_logger(__name__)

# Cache for service status to avoid slow checks on every search
_service_status_cache: Optional[Tuple[bool, float]] = None  # (is_running, timestamp)
_CACHE_TTL = 2.0  # Cache for 2 seconds - fast enough for rapid searches, fresh enough

# Service configuration
SERVICE_NAME = "FastSearchMCP"
SERVICE_EXECUTABLE = (
    Path(__file__).parent.parent.parent
    / "service"
    / "build"
    / "bin"
    / "Release"
    / "FastSearchServiceNew.exe"
)


def is_service_running() -> bool:
    """Check if the FastSearch C++ service is running (fast, cached check).

    Uses a fast pipe connection attempt first (fails immediately if service is down),
    with caching to avoid repeated checks. Falls back to process check only if needed.

    Returns:
        bool: True if the service is running, False otherwise
    """
    global _service_status_cache

    # Check cache first (fast path for repeated calls)
    now = time.time()
    if _service_status_cache is not None:
        cached_status, cache_time = _service_status_cache
        if now - cache_time < _CACHE_TTL:
            return cached_status

    # Fast check: Try to connect to pipe (fails immediately if service is down)
    # This is much faster than tasklist
    try:
        import pywintypes
        import win32file

        # Try to open pipe - this fails fast (ERROR_FILE_NOT_FOUND = 2) if service is down
        handle = win32file.CreateFile(
            get_pipe_name(),
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )
        # If we got here, pipe exists and service is running
        win32file.CloseHandle(handle)
        _service_status_cache = (True, now)
        return True
    except pywintypes.error as e:
        if e.winerror == 2:  # ERROR_FILE_NOT_FOUND - pipe doesn't exist, service is down
            _service_status_cache = (False, now)
            return False
        # Other errors might mean service is running but busy - fall through to process check
        logger.debug(f"Pipe check ambiguous (error {e.winerror}), falling back to process check")
    except Exception as e:
        logger.debug(f"Pipe check failed: {e}, falling back to process check")

    # Fallback: Check process list (slower, but more reliable for edge cases)
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq FastSearchServiceNew.exe"],
            capture_output=True,
            text=True,
            timeout=2,  # Reduced timeout - 2 seconds max
        )
        is_running = "FastSearchServiceNew.exe" in result.stdout
        _service_status_cache = (is_running, now)
        return is_running
    except subprocess.TimeoutExpired:
        # tasklist timed out - assume service is not running to avoid blocking
        logger.warning("Service check timed out, assuming service is not running")
        _service_status_cache = (False, now)
        return False
    except Exception as e:
        logger.debug(f"Error checking service status: {e}")
        _service_status_cache = (False, now)
        return False


async def get_service_status() -> Dict[str, Any]:
    """Get detailed status of the FastSearch C++ service.

    Returns:
        Dict containing service status information
    """
    try:
        # Check if service executable exists
        if not SERVICE_EXECUTABLE.exists():
            return {
                "running": False,
                "error": "Service executable not found",
                "executable_path": str(SERVICE_EXECUTABLE),
            }

        # Check if service process is running
        running = is_service_running()

        # Try to get service info via named pipe if running
        pipe_info = None
        if running:
            try:
                pipe_info = await get_service_info_via_pipe()
            except Exception as e:
                logger.debug(f"Could not get pipe info: {e}")

        # Try to get service info from Windows Service Manager
        try:
            result = await asyncio.to_thread(
                subprocess.run, ["sc", "query", SERVICE_NAME], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                # Parse service status from sc query output
                status_lines = result.stdout.split("\n")
                state = "UNKNOWN"
                for line in status_lines:
                    if "STATE" in line:
                        state = line.split(":")[-1].strip()
                        break

                return {
                    "running": running,
                    "service_state": state,
                    "executable_path": str(SERVICE_EXECUTABLE),
                    "pipe_name": get_pipe_name(),
                    "pipe_info": pipe_info,
                    "pipe_connected": pipe_info is not None,
                }
            else:
                return {
                    "running": running,
                    "error": "Service not installed",
                    "executable_path": str(SERVICE_EXECUTABLE),
                    "pipe_name": get_pipe_name(),
                    "pipe_info": pipe_info,
                    "pipe_connected": pipe_info is not None,
                }
        except Exception as e:
            logger.debug(f"Error querying service: {e}")
            return {
                "running": running,
                "error": f"Service query failed: {e}",
                "executable_path": str(SERVICE_EXECUTABLE),
                "pipe_name": get_pipe_name(),
                "pipe_info": pipe_info,
                "pipe_connected": pipe_info is not None,
            }

    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return {"running": False, "error": str(e), "executable_path": str(SERVICE_EXECUTABLE)}


async def search_files(
    pattern: str,
    directory: str = ".",
    max_results: int = 100,
    pagination_mode: Optional[str] = None,
    page: int = 1,
    page_size: int = 1000,
) -> Dict[str, Any]:
    """Search for files using the FastSearch C++ service via direct NTFS MFT access.

    This function REQUIRES the FastSearch service to be running. It does NOT fall back
    to treewalking as that violates the architecture (direct MFT access only).

    Args:
        pattern: Search pattern (glob or regex)
        directory: Directory to search in
        max_results: Maximum number of results (0 = unlimited, capped at 10M)
        pagination_mode: Pagination mode - "offset" for page-based, None for all results
        page: Page number (1-indexed) for offset pagination
        page_size: Results per page for offset pagination

    Returns:
        Dictionary containing:
            - results: List of file information dictionaries
            - count: Number of results
            - pagination: Pagination metadata (if pagination_mode="offset") or None

    Raises:
        RuntimeError: If the service is not available (no fallback to treewalk)
    """
    try:
        # Check if service is running
        if not is_service_running():
            error_msg = (
                "❌ FastSearch service is not running.\n\n"
                "The FastSearch MCP requires the FastSearch Windows service to be "
                "installed and running for direct NTFS MFT access. Without the service, "
                "file searches cannot be performed.\n\n"
                "To fix this:\n"
                "1. Check if the service is installed: Open Windows Services "
                "(Win+R → services.msc)\n"
                "2. Look for 'FastSearch MCP Service' or 'FastSearchMCP' in the list\n"
                "3. If installed but stopped: Right-click → Start\n"
                "4. If not installed: Run the installer as administrator\n\n"
                "You can also use the 'service_status' tool to check the current "
                "service status."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Try to communicate with the service via named pipe
        try:
            logger.info(f"Searching via NTFS MFT: pattern='{pattern}', directory='{directory}'")
            result = await search_files_via_pipe(
                pattern, directory, max_results, pagination_mode=pagination_mode, page=page, page_size=page_size
            )
            if result is None:
                error_msg = "No response from FastSearch service."
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            if result.get("error"):
                error_msg = result.get("error", "Search failed")
                logger.error(f"MFT search error: {error_msg}")
                raise RuntimeError(error_msg)
            if result.get("results") is not None:
                logger.info(f"MFT search completed: {result.get('count', 0)} files found")
                return result
            else:
                error_msg = (
                    "❌ No response from FastSearch service.\n\n"
                    "The FastSearch service appears to be running but is not "
                    "responding to requests. This may indicate the service is hung "
                    "or experiencing issues.\n\n"
                    "To troubleshoot:\n"
                    "1. Check service status using the 'service_status' tool\n"
                    "2. Try restarting the service: Use 'restart_service' tool "
                    "or Windows Services\n"
                    "3. Check service logs: Use 'get_service_logs' tool\n"
                    "4. If the issue persists, restart the service manually "
                    "as administrator"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        except RuntimeError:
            # Re-raise RuntimeError (our own errors)
            raise
        except Exception as e:
            error_msg = (
                f"❌ Named pipe communication failed: {e}\n\n"
                "The FastSearch service could not be reached via the named pipe. "
                "This usually means:\n"
                "- The service is not running (check with 'service_status' tool)\n"
                "- The service is hung or crashed (try restarting it)\n"
                "- Permission issues (ensure service is running as LocalSystem)\n\n"
                "To fix:\n"
                "1. Check service status: Use 'service_status' tool\n"
                "2. Restart the service: Use 'restart_service' tool or Windows Services\n"
                "3. Check service logs: Use 'get_service_logs' tool for error details"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    except RuntimeError:
        # Re-raise our errors
        raise
    except Exception as e:
        error_msg = f"File search failed: {e}. Service may not be available."
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def start_service() -> bool:
    """Start the FastSearch C++ service.

    Returns:
        bool: True if service started successfully, False otherwise
    """
    try:
        # Check if service executable exists
        if not SERVICE_EXECUTABLE.exists():
            logger.error(f"Service executable not found: {SERVICE_EXECUTABLE}")
            return False

        # Try to start the service using sc.exe
        result = await asyncio.to_thread(
            subprocess.run, ["sc", "start", SERVICE_NAME], capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            logger.info("FastSearch service started successfully")
            return True
        else:
            logger.error(f"Failed to start service: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error starting service: {e}")
        return False


async def stop_service() -> bool:
    """Stop the FastSearch C++ service.

    Returns:
        bool: True if service stopped successfully, False otherwise
    """
    try:
        # Try to stop the service using sc.exe
        result = await asyncio.to_thread(
            subprocess.run, ["sc", "stop", SERVICE_NAME], capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            logger.info("FastSearch service stopped successfully")
            return True
        else:
            logger.error(f"Failed to stop service: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error stopping service: {e}")
        return False


async def test_service_connection() -> Dict[str, Any]:
    """Test the connection to the FastSearch service.

    Returns:
        Dict containing connection test results
    """
    try:
        # Check if service is running
        running = is_service_running()

        # Test named pipe connection
        pipe_connected = False
        if running:
            pipe_connected = await test_pipe_connection()

        return {
            "service_running": running,
            "pipe_connected": pipe_connected,
            "executable_exists": SERVICE_EXECUTABLE.exists(),
            "executable_path": str(SERVICE_EXECUTABLE),
            "pipe_name": get_pipe_name(),
        }

    except Exception as e:
        logger.error(f"Service connection test failed: {e}")
        return {"service_running": False, "pipe_connected": False, "error": str(e)}
