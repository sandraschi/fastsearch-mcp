"""
IPC Client for FastSearch C++ Service.

This module provides communication between the Python FastMCP server
and the C++ Windows service using named pipes.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
import win32pipe
import win32file
import pywintypes

logger = logging.getLogger(__name__)


class FastSearchServiceClient:
    """Client for communicating with the FastSearch C++ Windows service."""
    
    def __init__(self, pipe_name: str = r"\\.\pipe\FastSearchMCPService"):
        """Initialize the service client."""
        self.pipe_name = pipe_name
        self.timeout = 5000  # 5 seconds timeout
        self.max_retries = 3
        
    def _connect_to_service(self) -> Optional[Any]:
        """Connect to the FastSearch service via named pipe."""
        try:
            # Try to connect to the named pipe
            pipe_handle = win32file.CreateFile(
                self.pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,  # No sharing
                None,  # Default security
                win32file.OPEN_EXISTING,
                0,  # No flags
                None  # No template
            )
            
            logger.info(f"Connected to FastSearch service via {self.pipe_name}")
            return pipe_handle
            
        except pywintypes.error as e:
            if e.winerror == 2:  # ERROR_FILE_NOT_FOUND
                logger.warning("FastSearch service is not running or pipe not available")
            else:
                logger.error(f"Failed to connect to service: {e}")
            return None
    
    def _send_request(self, pipe_handle: Any, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a request to the service and get response."""
        try:
            # Serialize request to JSON
            request_json = json.dumps(request)
            request_bytes = request_json.encode('utf-8')
            
            # Send request
            win32file.WriteFile(pipe_handle, request_bytes)
            
            # Read response
            result, response_bytes = win32file.ReadFile(pipe_handle, 4096)
            response_json = response_bytes.decode('utf-8')
            
            # Parse response
            response = json.loads(response_json)
            return response
            
        except Exception as e:
            logger.error(f"Error communicating with service: {e}")
            return None
    
    def search_files(self, pattern: str, directory: str = ".", max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search for files using the C++ service.
        
        Args:
            pattern: Search pattern (glob or regex)
            directory: Directory to search in
            max_results: Maximum number of results
            
        Returns:
            List of file information dictionaries
        """
        request = {
            "action": "search_files",
            "pattern": pattern,
            "directory": directory,
            "max_results": max_results
        }
        
        for attempt in range(self.max_retries):
            pipe_handle = self._connect_to_service()
            if pipe_handle is None:
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying connection to service (attempt {attempt + 2})")
                    time.sleep(1)
                    continue
                else:
                    logger.error("Failed to connect to service after all retries")
                    return []
            
            try:
                response = self._send_request(pipe_handle, request)
                if response and response.get("success"):
                    return response.get("files", [])
                else:
                    logger.error(f"Service returned error: {response.get('error', 'Unknown error')}")
                    return []
                    
            except Exception as e:
                logger.error(f"Error during search: {e}")
                return []
                
            finally:
                try:
                    win32file.CloseHandle(pipe_handle)
                except:
                    pass
        
        return []
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get the status of the FastSearch service."""
        request = {
            "action": "get_status"
        }
        
        pipe_handle = self._connect_to_service()
        if pipe_handle is None:
            return {
                "running": False,
                "error": "Service not accessible"
            }
        
        try:
            response = self._send_request(pipe_handle, request)
            if response:
                return {
                    "running": True,
                    "status": response.get("status", "unknown"),
                    "version": response.get("version", "unknown"),
                    "uptime": response.get("uptime", 0)
                }
            else:
                return {
                    "running": False,
                    "error": "No response from service"
                }
                
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                "running": False,
                "error": str(e)
            }
            
        finally:
            try:
                win32file.CloseHandle(pipe_handle)
            except:
                pass
    
    def test_connection(self) -> bool:
        """Test if the service is accessible."""
        status = self.get_service_status()
        return status.get("running", False)


# Global service client instance
_service_client: Optional[FastSearchServiceClient] = None


def get_service_client() -> FastSearchServiceClient:
    """Get the global service client instance."""
    global _service_client
    if _service_client is None:
        _service_client = FastSearchServiceClient()
    return _service_client


def search_files_via_service(pattern: str, directory: str = ".", max_results: int = 100) -> List[Dict[str, Any]]:
    """Search files using the C++ service."""
    client = get_service_client()
    return client.search_files(pattern, directory, max_results)


def is_service_running() -> bool:
    """Check if the FastSearch service is running."""
    client = get_service_client()
    return client.test_connection()
