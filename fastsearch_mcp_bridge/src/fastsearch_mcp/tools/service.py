"""
Service management tools for FastSearch MCP.

This module provides tools for managing the FastSearch service on Windows,
including starting, stopping, and checking the status of the service.
"""

import asyncio
import ctypes
import os
import platform
import subprocess
import sys
import winreg
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import psutil
import win32serviceutil
import win32service
import win32event
import servicemanager
import winerror
from win32com.shell import shell, shellcon

from ..exceptions import McpError
from . import tool, ToolRegistry

# Constants
SERVICE_NAME = "FastSearchService"
SERVICE_DISPLAY_NAME = "FastSearch NTFS Indexing Service"
SERVICE_DESCRIPTION = "Provides fast NTFS file system indexing and search capabilities."

class ServiceError(McpError):
    """Base class for service-related errors."""
    pass

def _is_admin() -> bool:
    """Check if the current process is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False

def _get_service_executable() -> Path:
    """Get the path to the service executable."""
    # Try to get the path from the registry
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            f"SYSTEM\\CurrentControlSet\\Services\\{SERVICE_NAME}",
        ) as key:
            path = winreg.QueryValueEx(key, "ImagePath")[0]
            # Remove quotes if present
            path = path.strip('"')
            return Path(path).resolve()
    except WindowsError:
        pass
    
    # Fall back to default location
    return Path(sys.executable).parent / "fastsearch-service.exe"

@tool("service.status", "Get the status of the FastSearch service")
async def get_service_status() -> Dict[str, Union[str, bool, int]]:
    """
    Get the current status of the FastSearch service.
    
    Returns:
        Dictionary containing service status information
    """
    try:
        status = win32serviceutil.QueryServiceStatus(SERVICE_NAME)
        status_codes = {
            win32service.SERVICE_STOPPED: "stopped",
            win32service.SERVICE_START_PENDING: "starting",
            win32service.SERVICE_STOP_PENDING: "stopping",
            win32service.SERVICE_RUNNING: "running",
            win32service.SERVICE_CONTINUE_PENDING: "resuming",
            win32service.SERVICE_PAUSE_PENDING: "pausing",
            win32service.SERVICE_PAUSED: "paused"
        }
        
        return {
            "status": status_codes.get(status[1], "unknown"),
            "pid": status[8] if status[1] == win32service.SERVICE_RUNNING else None,
            "can_control": _is_admin()
        }
    except Exception as e:
        if hasattr(e, 'winerror') and e.winerror == winerror.ERROR_SERVICE_DOES_NOT_EXIST:
            return {"status": "not_installed", "can_install": _is_admin()}
        raise ServiceError(f"Failed to get service status: {e}")

@tool("service.start", "Start the FastSearch service")
async def start_service() -> Dict[str, Union[str, bool]]:
    """
    Start the FastSearch service.
    
    Returns:
        Dictionary with operation result
    """
    if not _is_admin():
        raise ServiceError("Administrator privileges are required to start the service")
    
    try:
        win32serviceutil.StartService(SERVICE_NAME)
        return {"success": True, "message": "Service started successfully"}
    except Exception as e:
        raise ServiceError(f"Failed to start service: {e}")

@tool("service.stop", "Stop the FastSearch service")
async def stop_service() -> Dict[str, Union[str, bool]]:
    """
    Stop the FastSearch service.
    
    Returns:
        Dictionary with operation result
    """
    if not _is_admin():
        raise ServiceError("Administrator privileges are required to stop the service")
    
    try:
        win32serviceutil.StopService(SERVICE_NAME)
        return {"success": True, "message": "Service stopped successfully"}
    except Exception as e:
        raise ServiceError(f"Failed to stop service: {e}")

@tool("service.restart", "Restart the FastSearch service")
async def restart_service() -> Dict[str, Union[str, bool]]:
    """
    Restart the FastSearch service.
    
    Returns:
        Dictionary with operation result
    """
    if not _is_admin():
        raise ServiceError("Administrator privileges are required to restart the service")
    
    try:
        win32serviceutil.RestartService(SERVICE_NAME)
        return {"success": True, "message": "Service restarted successfully"}
    except Exception as e:
        raise ServiceError(f"Failed to restart service: {e}")

@tool("service.install", "Install the FastSearch service")
async def install_service(
    executable_path: Optional[str] = None,
    auto_start: bool = True
) -> Dict[str, Union[str, bool]]:
    """
    Install the FastSearch service.
    
    Args:
        executable_path: Path to the service executable (default: auto-detect)
        auto_start: Whether to start the service after installation
        
    Returns:
        Dictionary with operation result
    """
    if not _is_admin():
        raise ServiceError("Administrator privileges are required to install the service")
    
    try:
        if not executable_path:
            executable_path = str(_get_service_executable())
        
        # Create the service
        win32serviceutil.InstallService(
            None,  # Use default service manager
            SERVICE_NAME,
            SERVICE_DISPLAY_NAME,
            displayName=SERVICE_DISPLAY_NAME,
            description=SERVICE_DESCRIPTION,
            startType=win32service.SERVICE_AUTO_START if auto_start else win32service.SERVICE_DEMAND_START,
            exeName=f'"{executable_path}" service',
            exeArgs='run',
        )
        
        # Set service description
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                f"SYSTEM\\CurrentControlSet\\Services\\{SERVICE_NAME}",
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, "Description", 0, winreg.REG_SZ, SERVICE_DESCRIPTION)
        except Exception as e:
            logger.warning(f"Failed to set service description: {e}")
        
        if auto_start:
            win32serviceutil.StartService(SERVICE_NAME)
        
        return {
            "success": True,
            "message": f"Service installed successfully{' and started' if auto_start else ''}",
            "executable": executable_path
        }
    except Exception as e:
        raise ServiceError(f"Failed to install service: {e}")

@tool("service.uninstall", "Uninstall the FastSearch service")
async def uninstall_service() -> Dict[str, Union[str, bool]]:
    """
    Uninstall the FastSearch service.
    
    Returns:
        Dictionary with operation result
    """
    if not _is_admin():
        raise ServiceError("Administrator privileges are required to uninstall the service")
    
    try:
        # Stop the service first if it's running
        try:
            win32serviceutil.StopService(SERVICE_NAME)
        except Exception:
            pass  # Ignore errors if service is not running
        
        # Remove the service
        win32serviceutil.RemoveService(SERVICE_NAME)
        
        return {"success": True, "message": "Service uninstalled successfully"}
    except Exception as e:
        raise ServiceError(f"Failed to uninstall service: {e}")

@tool("service.repair", "Repair the FastSearch service installation")
async def repair_service() -> Dict[str, Union[str, bool]]:
    """
    Repair the FastSearch service installation.
    
    This will reinstall the service with default settings.
    
    Returns:
        Dictionary with operation result
    """
    if not _is_admin():
        raise ServiceError("Administrator privileges are required to repair the service")
    
    try:
        # Check if service exists
        try:
            status = win32serviceutil.QueryServiceStatus(SERVICE_NAME)
            is_installed = True
        except Exception:
            is_installed = False
        
        # Stop and uninstall if already installed
        if is_installed:
            try:
                win32serviceutil.StopService(SERVICE_NAME)
            except Exception:
                pass
            win32serviceutil.RemoveService(SERVICE_NAME)
        
        # Reinstall
        return await install_service()
    except Exception as e:
        raise ServiceError(f"Failed to repair service: {e}")

# Register all tools
def register_tools(registry: ToolRegistry) -> None:
    """Register all service management tools."""
    registry.register(get_service_status)
    registry.register(start_service)
    registry.register(stop_service)
    registry.register(restart_service)
    registry.register(install_service)
    registry.register(uninstall_service)
    registry.register(repair_service)
