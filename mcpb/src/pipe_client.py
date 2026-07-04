"""
Named pipe communication client for FastSearch C++ service.

This module provides real named pipe communication with the FastSearch C++ service
for high-performance NTFS MFT access.
"""

import asyncio
import json
import logging
import os
import struct
import sys
from typing import Any, Dict, List, Optional, Tuple

# Windows-specific imports
if sys.platform == "win32":
    try:
        import pywintypes
        import win32file
        import win32pipe

        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        logging.warning("Windows API modules not available. Named pipe communication disabled.")
else:
    WINDOWS_AVAILABLE = False

from .logging_config import get_logger

logger = get_logger(__name__)

# Service configuration: pipe name must match service\src\fastsearch_service.h kPipeName
# (L"\\\\.\\pipe\\FastSearchMCP"). Override with FASTSEARCH_PIPE_NAME if using a different build.
DEFAULT_PIPE_NAME = r"\\.\pipe\FastSearchMCP"
PIPE_TIMEOUT = 5000  # 5 seconds in milliseconds
MAX_PIPE_BUFFER = 65536  # 64KB buffer


def get_pipe_name() -> str:
    """Return the named pipe path. Use env FASTSEARCH_PIPE_NAME if set (e.g. if service uses a different name)."""
    return os.environ.get("FASTSEARCH_PIPE_NAME", DEFAULT_PIPE_NAME).strip() or DEFAULT_PIPE_NAME


# Backward compatibility
SERVICE_PIPE_NAME = DEFAULT_PIPE_NAME


class NamedPipeClient:
    """Client for communicating with FastSearch C++ service via named pipes."""

    def __init__(self, pipe_name: Optional[str] = None):
        self.pipe_name = pipe_name if pipe_name is not None else get_pipe_name()
        self.handle = None
        self.connected = False
        self.last_connect_error: Optional[Tuple[int, str]] = None  # (winerror, message) when connect fails

    async def connect(self, timeout: float = 5.0) -> bool:
        """Connect to the named pipe.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            bool: True if connected successfully, False otherwise
        """
        if not WINDOWS_AVAILABLE:
            logger.warning("Windows API not available, cannot connect to named pipe")
            return False

        self.last_connect_error = None
        try:
            # Try to open the named pipe (blocking Win32 call, run in executor)
            loop = asyncio.get_event_loop()
            self.handle = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: win32file.CreateFile(
                        self.pipe_name,
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                        0,
                        None,
                        win32file.OPEN_EXISTING,
                        0,
                        None,
                    ),
                ),
                timeout=timeout,
            )

            # Set pipe to message mode (blocking Win32 call, run in executor)
            await loop.run_in_executor(
                None,
                lambda: win32pipe.SetNamedPipeHandleState(
                    self.handle, win32pipe.PIPE_READMODE_MESSAGE, None, None
                ),
            )

            self.connected = True
            self.last_connect_error = None
            logger.info(f"Connected to named pipe: {self.pipe_name}")
            return True

        except asyncio.TimeoutError:
            self.last_connect_error = (0, f"Connection timed out after {timeout}s")
            logger.error(f"Connection to named pipe timed out after {timeout}s: {self.pipe_name}")
            self.connected = False
            return False
        except pywintypes.error as e:
            self.last_connect_error = (e.winerror, str(e))
            if e.winerror == 2:  # ERROR_FILE_NOT_FOUND
                logger.debug(f"Named pipe not found: {self.pipe_name} (error 2). Set FASTSEARCH_PIPE_NAME if service uses another name.")
            else:
                logger.error(f"Failed to connect to named pipe: {e}")
            self.connected = False
            return False
        except Exception as e:
            self.last_connect_error = (0, str(e))
            logger.error(f"Unexpected error connecting to named pipe: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from the named pipe."""
        if self.handle and self.connected:
            try:
                win32file.CloseHandle(self.handle)
                logger.info("Disconnected from named pipe")
            except Exception as e:
                logger.error(f"Error closing named pipe handle: {e}")
            finally:
                self.handle = None
                self.connected = False

    async def send_request(
        self, request: Dict[str, Any], timeout: float = 10.0
    ) -> Optional[Dict[str, Any]]:
        """Send a request to the service and get the response.

        Args:
            request: Request dictionary to send
            timeout: Request timeout in seconds

        Returns:
            Response dictionary or None if failed
        """
        if not self.connected or not self.handle:
            logger.error("Not connected to named pipe")
            return None

        def _send_request_sync():
            """Synchronous I/O operations that need to run in executor."""
            try:
                # Check handle validity before use
                if not self.handle:
                    logger.error("Pipe handle is invalid")
                    return None

                # Serialize request (ensure_ascii=True to escape Unicode characters)
                request_data = json.dumps(request, ensure_ascii=True).encode("utf-8")
                request_length = len(request_data)

                # Send length prefix (4 bytes, little-endian)
                length_bytes = struct.pack("<I", request_length)
                win32file.WriteFile(self.handle, length_bytes)

                # Send request data
                win32file.WriteFile(self.handle, request_data)

                # Flush the pipe
                win32file.FlushFileBuffers(self.handle)

                logger.debug(f"Sent request: {request}")

                # Read response length
                try:
                    response_length_bytes = win32file.ReadFile(self.handle, 4)[1]
                except pywintypes.error as e:
                    if e.winerror == 6:  # ERROR_INVALID_HANDLE
                        logger.error(
                            "Pipe handle became invalid during read "
                            "(service may have closed connection)"
                        )
                        self.connected = False
                    raise

                response_length = struct.unpack("<I", response_length_bytes)[0]

                if response_length > MAX_PIPE_BUFFER:
                    logger.error(f"Response too large: {response_length} bytes")
                    return None

                # Read response data
                try:
                    response_data = win32file.ReadFile(self.handle, response_length)[1]
                except pywintypes.error as e:
                    if e.winerror == 6:  # ERROR_INVALID_HANDLE
                        logger.error(
                            "Pipe handle became invalid during read "
                            "(service may have closed connection)"
                        )
                        self.connected = False
                    raise

                response = json.loads(response_data.decode("utf-8"))

                logger.debug(f"Received response: {response}")
                return response

            except pywintypes.error as e:
                error_code = e.winerror if hasattr(e, 'winerror') else 0
                if error_code == 6:  # ERROR_INVALID_HANDLE
                    logger.error(f"Pipe handle is invalid: {e}")
                else:
                    logger.error(f"Named pipe communication error: {e}")
                if self.handle:
                    try:
                        win32file.CloseHandle(self.handle)
                    except Exception:
                        pass
                    self.handle = None
                self.connected = False
                return None
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode response JSON: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in named pipe communication: {e}")
                return None

        try:
            # Run blocking I/O in executor with timeout
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, _send_request_sync),
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError:
            logger.error(f"Request timed out after {timeout} seconds: {request}")
            # Mark connection as potentially invalid after timeout
            # The service may still be processing, but we can't wait
            # Close the handle to allow reconnection
            if self.handle and self.connected:
                try:
                    win32file.CloseHandle(self.handle)
                except Exception:
                    pass
                self.handle = None
                self.connected = False
            return None
        except Exception as e:
            logger.error(f"Unexpected error in async request handling: {e}")
            return None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


async def search_files_via_pipe(
    pattern: str,
    directory: str = ".",
    max_results: int = 100,
    timeout: float = 120.0,
    pagination_mode: Optional[str] = None,
    page: int = 1,
    page_size: int = 1000,
) -> Dict[str, Any]:
    """Search for files using the C++ service via named pipe.

    Args:
        pattern: Search pattern (glob or regex)
        directory: Directory to search in
        max_results: Maximum number of results (0 = unlimited, capped at 10M)
        timeout: Request timeout in seconds (default: 120.0)
        pagination_mode: Pagination mode - "offset" for page-based, None for all results
        page: Page number (1-indexed) for offset pagination
        page_size: Results per page for offset pagination

    Returns:
        Dictionary containing:
            - results: List of file information dictionaries
            - count: Number of results in this response
            - pagination: Pagination metadata (if pagination_mode is "offset") or None
    """
    if not WINDOWS_AVAILABLE:
        logger.warning("Windows API not available, cannot use named pipe communication")
        return {"results": [], "count": 0, "pagination": None, "error": "Windows API not available"}

    async with NamedPipeClient() as client:
        if not client.connected:
            logger.warning("Could not connect to FastSearch service via named pipe")
            return {"results": [], "count": 0, "pagination": None, "error": "Could not connect to FastSearch service via named pipe"}

        request = {
            "command": "search_files",
            "pattern": pattern,
            "directory": directory,
            "max_results": max_results,
        }
        
        # Add pagination parameters if requested
        if pagination_mode == "offset":
            request["pagination_mode"] = "offset"
            request["page"] = page
            request["page_size"] = page_size

        response = await client.send_request(request, timeout=timeout)
        if response and response.get("success"):
            return {
                "results": response.get("results", []),
                "count": response.get("count", 0),
                "pagination": response.get("pagination"),
            }
        else:
            error_msg = response.get("error", "Unknown error") if response else "No response"
            logger.error(f"File search failed: {error_msg}")
            return {"results": [], "count": 0, "pagination": None, "error": error_msg}


async def get_service_info_via_pipe() -> Optional[Dict[str, Any]]:
    """Get service information via named pipe.

    Returns:
        Service information dictionary or None if failed
    """
    if not WINDOWS_AVAILABLE:
        logger.warning("Windows API not available, cannot use named pipe communication")
        return None

    async with NamedPipeClient() as client:
        if not client.connected:
            logger.warning("Could not connect to FastSearch service via named pipe")
            return None

        request = {"command": "get_service_info"}

        response = await client.send_request(request)
        if response and response.get("success"):
            return response.get("info", {})
        else:
            error_msg = response.get("error", "Unknown error") if response else "No response"
            logger.error(f"Get service info failed: {error_msg}")
            return None


async def test_pipe_connection() -> bool:
    """Test if the named pipe connection works.

    Returns:
        bool: True if connection successful, False otherwise
    """
    diag = await test_pipe_connection_with_diagnostics()
    return bool(diag.get("connected") and diag.get("ping_ok"))


async def test_pipe_connection_with_diagnostics() -> Dict[str, Any]:
    """Test pipe connection and return diagnostics for UI (error code, message, pipe name).

    Returns:
        dict: connected (bool), ping_ok (bool), pipe_name (str),
              error_code (int | None), error_message (str | None)
    """
    pipe_name = get_pipe_name()
    out: Dict[str, Any] = {
        "connected": False,
        "ping_ok": False,
        "pipe_name": pipe_name,
        "error_code": None,
        "error_message": None,
    }
    if not WINDOWS_AVAILABLE:
        out["error_message"] = "Windows API not available"
        return out

    try:
        async with NamedPipeClient() as client:
            if not client.connected:
                if client.last_connect_error:
                    out["error_code"] = client.last_connect_error[0]
                    out["error_message"] = client.last_connect_error[1]
                else:
                    out["error_message"] = "Connect failed (no error details)"
                return out
            out["connected"] = True

            request = {"command": "ping"}
            response = await client.send_request(request, timeout=2.0)
            out["ping_ok"] = response is not None and response.get("success", False)
            if not out["ping_ok"] and response:
                out["error_message"] = response.get("error", "Ping did not return success")
            return out
    except Exception as e:
        out["error_message"] = str(e)
        return out
