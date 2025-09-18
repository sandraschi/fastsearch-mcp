"""
Named pipe communication client for FastSearch C++ service.

This module provides real named pipe communication with the FastSearch C++ service
for high-performance NTFS MFT access.
"""

import asyncio
import json
import logging
import struct
import time
from typing import Dict, List, Optional, Any, Union
import os
import sys

# Windows-specific imports
if sys.platform == "win32":
    try:
        import win32file
        import win32pipe
        import pywintypes
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        logging.warning("Windows API modules not available. Named pipe communication disabled.")
else:
    WINDOWS_AVAILABLE = False

from .logging_config import get_logger

logger = get_logger(__name__)

# Service configuration
SERVICE_PIPE_NAME = r"\\.\pipe\FastSearchMCP"
PIPE_TIMEOUT = 5000  # 5 seconds in milliseconds
MAX_PIPE_BUFFER = 65536  # 64KB buffer


class NamedPipeClient:
    """Client for communicating with FastSearch C++ service via named pipes."""
    
    def __init__(self, pipe_name: str = SERVICE_PIPE_NAME):
        self.pipe_name = pipe_name
        self.handle = None
        self.connected = False
        
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
            
        try:
            # Try to open the named pipe
            self.handle = win32file.CreateFile(
                self.pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            
            # Set pipe to message mode
            win32pipe.SetNamedPipeHandleState(
                self.handle,
                win32pipe.PIPE_READMODE_MESSAGE,
                None,
                None
            )
            
            self.connected = True
            logger.info(f"Connected to named pipe: {self.pipe_name}")
            return True
            
        except pywintypes.error as e:
            if e.winerror == 2:  # ERROR_FILE_NOT_FOUND
                logger.debug(f"Named pipe not found: {self.pipe_name}")
            else:
                logger.error(f"Failed to connect to named pipe: {e}")
            self.connected = False
            return False
        except Exception as e:
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
    
    async def send_request(self, request: Dict[str, Any], timeout: float = 10.0) -> Optional[Dict[str, Any]]:
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
            
        try:
            # Serialize request
            request_data = json.dumps(request).encode('utf-8')
            request_length = len(request_data)
            
            # Send length prefix (4 bytes, little-endian)
            length_bytes = struct.pack('<I', request_length)
            win32file.WriteFile(self.handle, length_bytes)
            
            # Send request data
            win32file.WriteFile(self.handle, request_data)
            
            # Flush the pipe
            win32file.FlushFileBuffers(self.handle)
            
            logger.debug(f"Sent request: {request}")
            
            # Read response length
            response_length_bytes = win32file.ReadFile(self.handle, 4)[1]
            response_length = struct.unpack('<I', response_length_bytes)[0]
            
            if response_length > MAX_PIPE_BUFFER:
                logger.error(f"Response too large: {response_length} bytes")
                return None
            
            # Read response data
            response_data = win32file.ReadFile(self.handle, response_length)[1]
            response = json.loads(response_data.decode('utf-8'))
            
            logger.debug(f"Received response: {response}")
            return response
            
        except pywintypes.error as e:
            logger.error(f"Named pipe communication error: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode response JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in named pipe communication: {e}")
            return None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


async def search_files_via_pipe(pattern: str, directory: str = ".", max_results: int = 100) -> List[Dict[str, Any]]:
    """Search for files using the C++ service via named pipe.
    
    Args:
        pattern: Search pattern (glob or regex)
        directory: Directory to search in
        max_results: Maximum number of results
        
    Returns:
        List of file information dictionaries
    """
    if not WINDOWS_AVAILABLE:
        logger.warning("Windows API not available, cannot use named pipe communication")
        return []
    
    async with NamedPipeClient() as client:
        if not client.connected:
            logger.warning("Could not connect to FastSearch service via named pipe")
            return []
        
        request = {
            "command": "search_files",
            "pattern": pattern,
            "directory": directory,
            "max_results": max_results
        }
        
        response = await client.send_request(request)
        if response and response.get("success"):
            return response.get("results", [])
        else:
            error_msg = response.get("error", "Unknown error") if response else "No response"
            logger.error(f"File search failed: {error_msg}")
            return []


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
        
        request = {
            "command": "get_service_info"
        }
        
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
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        async with NamedPipeClient() as client:
            if not client.connected:
                return False
            
            # Send a simple ping request
            request = {"command": "ping"}
            response = await client.send_request(request, timeout=2.0)
            
            return response is not None and response.get("success", False)
            
    except Exception as e:
        logger.debug(f"Pipe connection test failed: {e}")
        return False