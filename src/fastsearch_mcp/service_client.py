"""
Service client for communicating with the FastSearch C++ service.

This module provides functions to communicate with the FastSearch C++ service
via named pipes for NTFS MFT access.
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from .logging_config import get_logger
from .pipe_client import NamedPipeClient, search_files_via_pipe, get_service_info_via_pipe, test_pipe_connection

logger = get_logger(__name__)

# Service configuration
SERVICE_NAME = "FastSearchMCP"
SERVICE_PIPE_NAME = r"\\.\pipe\FastSearchMCP"
SERVICE_EXECUTABLE = Path(__file__).parent.parent.parent / "service" / "build" / "bin" / "Release" / "FastSearchServiceNew.exe"


def is_service_running() -> bool:
    """Check if the FastSearch C++ service is running.
    
    Returns:
        bool: True if the service is running, False otherwise
    """
    try:
        # Check if the service process is running
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq FastSearchServiceNew.exe"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "FastSearchServiceNew.exe" in result.stdout
    except Exception as e:
        logger.debug(f"Error checking service status: {e}")
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
                "executable_path": str(SERVICE_EXECUTABLE)
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
            result = subprocess.run(
                ["sc", "query", SERVICE_NAME],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse service status from sc query output
                status_lines = result.stdout.split('\n')
                state = "UNKNOWN"
                for line in status_lines:
                    if "STATE" in line:
                        state = line.split(":")[-1].strip()
                        break
                
                return {
                    "running": running,
                    "service_state": state,
                    "executable_path": str(SERVICE_EXECUTABLE),
                    "pipe_name": SERVICE_PIPE_NAME,
                    "pipe_info": pipe_info,
                    "pipe_connected": pipe_info is not None
                }
            else:
                return {
                    "running": running,
                    "error": "Service not installed",
                    "executable_path": str(SERVICE_EXECUTABLE),
                    "pipe_info": pipe_info,
                    "pipe_connected": pipe_info is not None
                }
        except Exception as e:
            logger.debug(f"Error querying service: {e}")
            return {
                "running": running,
                "error": f"Service query failed: {e}",
                "executable_path": str(SERVICE_EXECUTABLE),
                "pipe_info": pipe_info,
                "pipe_connected": pipe_info is not None
            }
            
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return {
            "running": False,
            "error": str(e),
            "executable_path": str(SERVICE_EXECUTABLE)
        }


async def search_files(pattern: str, directory: str = ".", max_results: int = 100) -> List[Dict[str, Any]]:
    """Search for files using the FastSearch C++ service.
    
    Args:
        pattern: Search pattern (glob or regex)
        directory: Directory to search in
        max_results: Maximum number of results
        
    Returns:
        List of file information dictionaries
    """
    try:
        # Check if service is running
        if not is_service_running():
            logger.warning("FastSearch service is not running, using fallback search")
            return await _fallback_search(pattern, directory, max_results)
        
        # Try to communicate with the service via named pipe
        try:
            logger.info("Attempting to search files via named pipe")
            results = await search_files_via_pipe(pattern, directory, max_results)
            if results:
                logger.info(f"Found {len(results)} files via named pipe")
                return results
            else:
                logger.warning("No results from named pipe, using fallback")
                return await _fallback_search(pattern, directory, max_results)
        except Exception as e:
            logger.warning(f"Named pipe communication failed: {e}, using fallback")
            return await _fallback_search(pattern, directory, max_results)
            
    except Exception as e:
        logger.error(f"File search failed: {e}")
        return []


async def _fallback_search(pattern: str, directory: str = ".", max_results: int = 100) -> List[Dict[str, Any]]:
    """Fallback file search using Python's pathlib when service is not available.
    
    Args:
        pattern: Search pattern (glob)
        directory: Directory to search in
        max_results: Maximum number of results
        
    Returns:
        List of file information dictionaries
    """
    try:
        from pathlib import Path
        import fnmatch
        
        search_path = Path(directory).resolve()
        if not search_path.exists():
            logger.error(f"Search directory does not exist: {directory}")
            return []
        
        results = []
        count = 0
        
        # Simple glob-based search
        for file_path in search_path.rglob("*"):
            if count >= max_results:
                break
                
            if file_path.is_file():
                # Check if file matches pattern
                if fnmatch.fnmatch(file_path.name, pattern) or fnmatch.fnmatch(str(file_path), pattern):
                    try:
                        stat = file_path.stat()
                        results.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "created": stat.st_ctime,
                            "is_directory": False,
                            "method": "fallback_python"
                        })
                        count += 1
                    except Exception as e:
                        logger.debug(f"Error getting file info for {file_path}: {e}")
                        continue
        
        logger.info(f"Fallback search found {len(results)} files matching '{pattern}' in '{directory}'")
        return results
        
    except Exception as e:
        logger.error(f"Fallback search failed: {e}")
        return []


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
        result = subprocess.run(
            ["sc", "start", SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=30
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
        result = subprocess.run(
            ["sc", "stop", SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=30
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
            "pipe_name": SERVICE_PIPE_NAME
        }
        
    except Exception as e:
        logger.error(f"Service connection test failed: {e}")
        return {
            "service_running": False,
            "pipe_connected": False,
            "error": str(e)
        }