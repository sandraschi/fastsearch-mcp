"""IPC client for FastSearch Windows Service communication."""

import asyncio
import json
import logging
import os
import struct
from typing import Any, Dict, List, Optional, Tuple

import pywintypes
import win32file
import win32pipe
import win32security
from win32 import win32api

logger = logging.getLogger(__name__)

# Constants for pipe communication
PIPE_NAME = r"\\.\pipe\fastsearch-service"
BUFFER_SIZE = 65536
CONNECT_TIMEOUT = 5000  # ms
IO_TIMEOUT = 30000  # ms

# Message types
MSG_SEARCH = 1
MSG_STATUS = 2

# Response status codes
STATUS_OK = 0
STATUS_ERROR = 1
STATUS_UNAVAILABLE = 2


class IpcError(Exception):
    """Base exception for IPC errors."""
    pass


class IpcConnectionError(IpcError):
    """Raised when connection to the service fails."""
    pass


class IpcTimeoutError(IpcError):
    """Raised when an IPC operation times out."""
    pass


class IpcProtocolError(IpcError):
    """Raised for protocol-level errors."""
    pass


class FastSearchClient:
    """Client for communicating with the FastSearch Windows Service."""

    def __init__(self, pipe_name: str = PIPE_NAME):
        """Initialize the FastSearch client.
        
        Args:
            pipe_name: Name of the named pipe to connect to
        """
        self.pipe_name = pipe_name
        self.pipe_handle = None
        self.connected = False
        self._lock = asyncio.Lock()
        self._connect_task = None

    async def connect(self) -> None:
        """Connect to the FastSearch service.
        
        Raises:
            IpcConnectionError: If connection fails
        """
        async with self._lock:
            if self.connected:
                return

            try:
                # Try to open the named pipe
                self.pipe_handle = win32file.CreateFile(
                    self.pipe_name,
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0,  # No sharing
                    None,  # Default security
                    win32file.OPEN_EXISTING,
                    win32file.FILE_FLAG_OVERLAPPED,
                    None  # Template file
                )
                
                # Set read mode and blocking mode
                win32pipe.SetNamedPipeHandleState(
                    self.pipe_handle,
                    win32pipe.PIPE_READMODE_MESSAGE,
                    None,
                    None
                )
                
                self.connected = True
                logger.info(f"Connected to FastSearch service at {self.pipe_name}")
                
            except pywintypes.error as e:
                self.connected = False
                if self.pipe_handle:
                    win32file.CloseHandle(self.pipe_handle)
                    self.pipe_handle = None
                
                if e.winerror == 2:  # File not found
                    raise IpcConnectionError(
                        f"FastSearch service not found at {self.pipe_name}. "
                        "Is the service running?"
                    )
                elif e.winerror == 231:  # All pipe instances busy
                    raise IpcConnectionError(
                        "All FastSearch service instances are busy. Please try again later."
                    )
                else:
                    raise IpcConnectionError(
                        f"Failed to connect to FastSearch service: {e.strerror}"
                    ) from e

    async def disconnect(self) -> None:
        """Disconnect from the FastSearch service."""
        async with self._lock:
            if self.pipe_handle:
                win32file.CloseHandle(self.pipe_handle)
                self.pipe_handle = None
            self.connected = False

    async def _ensure_connected(self) -> None:
        """Ensure we're connected to the service."""
        if not self.connected:
            await self.connect()

    async def _send_message(self, message_type: int, data: bytes) -> bytes:
        """Send a message to the service and return the response.
        
        Args:
            message_type: Type of message (MSG_SEARCH, MSG_STATUS, etc.)
            data: Message payload
            
        Returns:
            Response data from the service
            
        Raises:
            IpcError: If communication fails
        """
        async with self._lock:
            await self._ensure_connected()
            
            # Prepare message header: 4 bytes for message type + 4 bytes for data length
            header = struct.pack("<II", message_type, len(data))
            message = header + data
            
            try:
                # Send the message
                _, err = win32file.WriteFile(self.pipe_handle, message)
                if err != 0:
                    raise IpcError(f"Failed to send message: Windows error {err}")
                
                # Read response header (8 bytes: 4 for status, 4 for length)
                hr, header_data = win32file.ReadFile(
                    self.pipe_handle, 8, None
                )
                if hr != 0:
                    raise IpcError(f"Failed to read response header: Windows error {hr}")
                
                status, length = struct.unpack("<II", header_data)
                
                # Read response data if any
                response_data = b""
                if length > 0:
                    hr, response_data = win32file.ReadFile(
                        self.pipe_handle, length, None
                    )
                    if hr != 0:
                        raise IpcError(f"Failed to read response data: Windows error {hr}")
                
                # Check status
                if status == STATUS_ERROR:
                    error_msg = response_data.decode('utf-8', errors='replace')
                    raise IpcError(f"Service error: {error_msg}")
                elif status == STATUS_UNAVAILABLE:
                    raise IpcError("Service temporarily unavailable")
                
                return response_data
                
            except pywintypes.error as e:
                self.connected = False
                if e.winerror == 109:  # Broken pipe
                    raise IpcConnectionError("Connection to service lost") from e
                elif e.winerror == 232:  # Pipe busy
                    raise IpcTimeoutError("Service request timed out") from e
                else:
                    raise IpcError(f"IPC communication error: {e.strerror}") from e

    async def search(
        self,
        pattern: str,
        search_type: str = "fuzzy",
        max_results: int = 50,
        **filters
    ) -> Dict[str, Any]:
        """Execute a search on the FastSearch service.
        
        Args:
            pattern: Search pattern
            search_type: Type of search (exact, glob, regex, fuzzy)
            max_results: Maximum number of results to return
            **filters: Additional search filters
            
        Returns:
            Search results as a dictionary
        """
        request = {
            "pattern": pattern,
            "type": search_type,
            "max_results": max(1, min(max_results, 1000)),  # Enforce reasonable limits
            "filters": filters or {}
        }
        
        try:
            response_data = await self._send_message(
                MSG_SEARCH,
                json.dumps(request).encode('utf-8')
            )
            return json.loads(response_data.decode('utf-8'))
            
        except json.JSONDecodeError as e:
            raise IpcProtocolError("Invalid response format from service") from e

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the FastSearch service.
        
        Returns:
            Service status information
        """
        try:
            response_data = await self._send_message(MSG_STATUS, b"")
            return json.loads(response_data.decode('utf-8'))
            
        except json.JSONDecodeError as e:
            raise IpcProtocolError("Invalid status response from service") from e

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    def __del__(self):
        """Ensure resources are cleaned up."""
        if hasattr(self, 'pipe_handle') and self.pipe_handle:
            win32file.CloseHandle(self.pipe_handle)
