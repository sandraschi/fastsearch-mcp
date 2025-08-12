"""Windows named pipe client for FastSearch service communication."""

import os
import json
import logging
import asyncio
import win32pipe, win32file, pywintypes
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

class PipeClientError(Exception):
    """Base exception for pipe client errors."""
    pass

class PipeClient:
    """Client for communicating with the FastSearch Windows service via named pipes."""
    
    def __init__(self, pipe_name: str = r"\\.\pipe\fastsearch-service"):
        """Initialize the pipe client.
        
        Args:
            pipe_name: Name of the named pipe to connect to.
        """
        self.pipe_name = pipe_name
        self.handle = None
        self._lock = asyncio.Lock()
    
    async def connect(self, timeout: float = 5.0) -> bool:
        """Connect to the named pipe.
        
        Args:
            timeout: Connection timeout in seconds.
            
        Returns:
            bool: True if connected successfully, False otherwise.
        """
        if self.handle is not None:
            return True
            
        try:
            # Use asyncio to run the blocking operation in a thread
            loop = asyncio.get_running_loop()
            self.handle = await loop.run_in_executor(
                None,
                self._connect_blocking
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to pipe: {e}")
            self.handle = None
            return False
    
    def _connect_blocking(self) -> int:
        """Blocking implementation of pipe connection."""
        try:
            # Try to open the named pipe
            handle = win32file.CreateFile(
                self.pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,  # No sharing
                None,  # Default security
                win32file.OPEN_EXISTING,
                0,  # Default attributes
                None  # No template file
            )
            return handle
        except pywintypes.error as e:
            if e.winerror == 2:  # File not found
                raise PipeClientError("FastSearch service is not running") from e
            raise PipeClientError(f"Failed to connect to pipe: {e}") from e
    
    async def close(self) -> None:
        """Close the pipe connection."""
        if self.handle is not None:
            try:
                # Use asyncio to run the blocking operation in a thread
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    win32file.CloseHandle,
                    self.handle
                )
            except Exception as e:
                logger.error(f"Error closing pipe: {e}")
            finally:
                self.handle = None
    
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a request to the service and get the response.
        
        Args:
            method: The method to call on the service.
            params: Optional parameters for the method.
            
        Returns:
            Dict[str, Any]: The response from the service.
            
        Raises:
            PipeClientError: If there's an error communicating with the service.
        """
        if self.handle is None:
            if not await self.connect():
                raise PipeClientError("Not connected to pipe")
        
        # Create the request
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        # Serialize the request to JSON
        request_data = json.dumps(request).encode('utf-8')
        
        # Add a newline terminator
        request_data = request_data + b"\n"
        
        async with self._lock:
            try:
                # Send the request
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    lambda: win32file.WriteFile(self.handle, request_data)
                )
                
                # Read the response
                response_data = await loop.run_in_executor(
                    None,
                    self._read_response_blocking
                )
                
                # Parse the response
                try:
                    response = json.loads(response_data)
                    if "error" in response:
                        raise PipeClientError(f"Service error: {response['error']}")
                    return response.get("result", {})
                except json.JSONDecodeError as e:
                    raise PipeClientError(f"Invalid JSON response: {response_data}") from e
                    
            except pywintypes.error as e:
                self.handle = None  # Mark as disconnected
                raise PipeClientError(f"Pipe communication error: {e}") from e
    
    def _read_response_blocking(self) -> str:
        """Blocking implementation of reading a response from the pipe."""
        if self.handle is None:
            raise PipeClientError("Not connected to pipe")
        
        buffer = bytearray()
        while True:
            try:
                # Read a chunk of data
                _, data = win32file.ReadFile(self.handle, 4096)
                if not data:
                    break
                    
                buffer.extend(data)
                
                # Check for newline terminator
                if buffer.endswith(b"\n"):
                    break
                    
            except pywintypes.error as e:
                if e.winerror != 109:  # ERROR_BROKEN_PIPE
                    raise
                break
        
        if not buffer:
            raise PipeClientError("Empty response from pipe")
            
        # Remove the newline terminator and decode
        return buffer.rstrip().decode('utf-8')
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not await self.connect():
            raise PipeClientError("Failed to connect to pipe")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
