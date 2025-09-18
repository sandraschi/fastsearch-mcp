"""Service management tool for Windows services."""
import asyncio
import ctypes
import json
import os
import platform
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import psutil
import win32service
import win32serviceutil
import winerror
from fastsearch_mcp.logging_config import get_logger
from fastsearch_mcp.tools.base import BaseTool, ToolCategory, ToolParameter, tool
from pywintypes import error as win32_error

logger = get_logger(__name__)

# Constants for service access rights
SERVICE_QUERY_CONFIG = 0x0001
SERVICE_CHANGE_CONFIG = 0x0002
SERVICE_QUERY_STATUS = 0x0004
SERVICE_START = 0x0010
SERVICE_STOP = 0x0020
SERVICE_ALL_ACCESS = 0xF01FF
SC_MANAGER_ALL_ACCESS = 0xF003F

class ServiceStatus(Enum):
    """Windows service status codes."""
    STOPPED = "STOPPED"
    START_PENDING = "START_PENDING"
    STOP_PENDING = "STOP_PENDING"
    RUNNING = "RUNNING"
    CONTINUE_PENDING = "CONTINUE_PENDING"
    PAUSE_PENDING = "PAUSE_PENDING"
    PAUSED = "PAUSED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_win32(cls, status_code: int) -> 'ServiceStatus':
        """Convert Windows service status code to ServiceStatus enum."""
        status_map = {
            win32service.SERVICE_STOPPED: cls.STOPPED,
            win32service.SERVICE_START_PENDING: cls.START_PENDING,
            win32service.SERVICE_STOP_PENDING: cls.STOP_PENDING,
            win32service.SERVICE_RUNNING: cls.RUNNING,
            win32service.SERVICE_CONTINUE_PENDING: cls.CONTINUE_PENDING,
            win32service.SERVICE_PAUSE_PENDING: cls.PAUSE_PENDING,
            win32service.SERVICE_PAUSED: cls.PAUSED,
        }
        return status_map.get(status_code, cls.UNKNOWN)

class ServiceStartupType(Enum):
    """Windows service startup types."""
    BOOT = "BOOT"
    SYSTEM = "SYSTEM"
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"
    DISABLED = "DISABLED"

    @classmethod
    def from_win32(cls, startup_type: int) -> 'ServiceStartupType':
        """Convert Windows service startup type to enum."""
        type_map = {
            win32service.SERVICE_BOOT_START: cls.BOOT,
            win32service.SERVICE_SYSTEM_START: cls.SYSTEM,
            win32service.SERVICE_AUTO_START: cls.AUTOMATIC,
            win32service.SERVICE_DEMAND_START: cls.MANUAL,
            win32service.SERVICE_DISABLED: cls.DISABLED,
        }
        return type_map.get(startup_type, cls.MANUAL)

@dataclass
class ServiceInfo:
    """Information about a Windows service."""
    name: str
    display_name: str
    status: ServiceStatus
    startup_type: ServiceStartupType
    binary_path: str
    description: str = ""
    pid: Optional[int] = None
    exit_code: Optional[int] = None
    process_name: Optional[str] = None
    username: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    delayed_start: bool = False
    error_control: str = "NORMAL"
    load_order_group: str = ""
    service_type: str = "WIN32_OWN_PROCESS"
    tag_id: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "status": self.status.value,
            "startup_type": self.startup_type.value,
            "binary_path": self.binary_path,
            "description": self.description,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "process_name": self.process_name,
            "username": self.username,
            "dependencies": self.dependencies,
            "delayed_start": self.delayed_start,
            "error_control": self.error_control,
            "load_order_group": self.load_order_group,
            "service_type": self.service_type,
            "tag_id": self.tag_id
        }
    
    @classmethod
    def from_win32_service(cls, service_name: str) -> Optional['ServiceInfo']:
        """Create ServiceInfo from Windows service name."""
        try:
            # Get service handle
            scm_handle = win32service.OpenSCManager(
                None, None, win32service.SC_MANAGER_CONNECT
            )
            
            try:
                service_handle = win32service.OpenService(
                    scm_handle, 
                    service_name, 
                    win32service.SERVICE_QUERY_CONFIG | 
                    win32service.SERVICE_QUERY_STATUS | 
                    win32service.SERVICE_ENUMERATE_DEPENDENTS
                )
                
                try:
                    # Get service config
                    config = win32service.QueryServiceConfig(service_handle)
                    status = win32service.QueryServiceStatusEx(service_handle)
                    
                    # Get service description
                    try:
                        description = win32service.QueryServiceConfig2(
                            service_handle, 
                            win32service.SERVICE_CONFIG_DESCRIPTION
                        )
                        description = description or ""
                    except Exception:
                        description = ""
                    
                    # Get service dependencies
                    try:
                        deps = win32service.EnumDependentServices(service_handle, win32service.SERVICE_ACTIVE)
                        dependencies = [dep[0] for dep in deps]
                    except Exception:
                        dependencies = []
                    
                    # Get process info if running
                    pid = status["ProcessId"] if "ProcessId" in status else None
                    process_name = None
                    username = None
                    
                    if pid and pid > 0:
                        try:
                            proc = psutil.Process(pid)
                            process_name = proc.name()
                            username = proc.username()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    return cls(
                        name=service_name,
                        display_name=config[0] or service_name,
                        status=ServiceStatus.from_win32(status["CurrentState"]),
                        startup_type=ServiceStartupType.from_win32(config[1]),
                        binary_path=config[3],
                        description=description,
                        pid=pid,
                        exit_code=status.get("Win32ExitCode"),
                        process_name=process_name,
                        username=username,
                        dependencies=dependencies,
                        delayed_start=bool(config[7] & 0x00000001),  # SERVICE_DELAYED_AUTO_START_INFO
                        service_type=cls._get_service_type_str(config[2]),
                        error_control=cls._get_error_control_str(config[4]),
                        load_order_group=config[5] or "",
                        tag_id=config[6] if len(config) > 6 else 0
                    )
                finally:
                    win32service.CloseServiceHandle(service_handle)
            finally:
                win32service.CloseServiceHandle(scm_handle)
        except Exception as e:
            logger.error(f"Error getting service info for {service_name}: {e}")
            return None
    
    @staticmethod
    def _get_service_type_str(service_type: int) -> str:
        """Convert service type to string."""
        types = []
        if service_type & win32service.SERVICE_KERNEL_DRIVER:
            types.append("KERNEL_DRIVER")
        if service_type & win32service.SERVICE_FILE_SYSTEM_DRIVER:
            types.append("FILE_SYSTEM_DRIVER")
        if service_type & win32service.SERVICE_WIN32_OWN_PROCESS:
            types.append("WIN32_OWN_PROCESS")
        if service_type & win32service.SERVICE_WIN32_SHARE_PROCESS:
            types.append("WIN32_SHARE_PROCESS")
        if service_type & win32service.SERVICE_INTERACTIVE_PROCESS:
            types.append("INTERACTIVE_PROCESS")
        return " | ".join(types) if types else str(service_type)
    
    @staticmethod
    def _get_error_control_str(error_control: int) -> str:
        """Convert error control to string."""
        error_controls = {
            win32service.SERVICE_ERROR_IGNORE: "IGNORE",
            win32service.SERVICE_ERROR_NORMAL: "NORMAL",
            win32service.SERVICE_ERROR_SEVERE: "SEVERE",
            win32service.SERVICE_ERROR_CRITICAL: "CRITICAL"
        }
        return error_controls.get(error_control, f"UNKNOWN({error_control})")

class ServiceManager:
    """Class for managing Windows services."""
    
    @staticmethod
    def get_services() -> List[ServiceInfo]:
        """Get all services on the system."""
        services = []
        scm_handle = win32service.OpenSCManager(
            None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE
        )
        
        try:
            # Get all services
            service_status = win32service.EnumServicesStatusEx(
                scm_handle,
                win32service.SERVICE_WIN32,
                win32service.SERVICE_STATE_ALL
            )
            
            for service in service_status:
                service_name = service[0]
                try:
                    service_info = ServiceInfo.from_win32_service(service_name)
                    if service_info:
                        services.append(service_info)
                except Exception as e:
                    logger.error(f"Error processing service {service_name}: {e}")
        finally:
            win32service.CloseServiceHandle(scm_handle)
        
        return services
    
    @staticmethod
    def get_service(service_name: str) -> Optional[ServiceInfo]:
        """Get information about a specific service."""
        return ServiceInfo.from_win32_service(service_name)
    
    @staticmethod
    def start_service(service_name: str, args: Optional[List[str]] = None, 
                     timeout: int = 30) -> Dict[str, Any]:
        """Start a Windows service.
        
        Args:
            service_name: Name of the service to start
            args: Optional list of arguments to pass to the service
            timeout: Maximum time to wait for the service to start (in seconds)
            
        Returns:
            Dict with status information
        """
        try:
            # Check if service exists and get current status
            service = ServiceManager.get_service(service_name)
            if not service:
                return {
                    "success": False,
                    "error": f"Service '{service_name}' not found",
                    "service": service_name,
                    "action": "start"
                }
            
            if service.status == ServiceStatus.RUNNING:
                return {
                    "success": True,
                    "message": f"Service '{service_name}' is already running",
                    "service": service_name,
                    "status": service.status.value,
                    "action": "start"
                }
            
            # Start the service
            start_time = time.time()
            win32serviceutil.StartService(service_name, " ".join(args or []))
            
            # Wait for the service to start
            while time.time() - start_time < timeout:
                service = ServiceManager.get_service(service_name)
                if not service:
                    return {
                        "success": False,
                        "error": f"Service '{service_name}' not found after start attempt",
                        "service": service_name,
                        "action": "start"
                    }
                
                if service.status == ServiceStatus.RUNNING:
                    return {
                        "success": True,
                        "message": f"Successfully started service '{service_name}'",
                        "service": service_name,
                        "status": service.status.value,
                        "pid": service.pid,
                        "elapsed_time": time.time() - start_time,
                        "action": "start"
                    }
                elif service.status == ServiceStatus.STOPPED:
                    return {
                        "success": False,
                        "error": f"Service '{service_name}' failed to start (status: {service.status.value})",
                        "service": service_name,
                        "status": service.status.value,
                        "exit_code": service.exit_code,
                        "elapsed_time": time.time() - start_time,
                        "action": "start"
                    }
                
                time.sleep(0.5)
            
            # If we get here, the service didn't start in time
            service = ServiceManager.get_service(service_name)
            return {
                "success": False,
                "error": f"Timeout waiting for service '{service_name}' to start",
                "service": service_name,
                "status": service.status.value if service else "UNKNOWN",
                "elapsed_time": time.time() - start_time,
                "action": "start"
            }
            
        except win32_error as e:
            error_msg = ServiceManager._get_win32_error_message(e)
            return {
                "success": False,
                "error": f"Failed to start service '{service_name}': {error_msg}",
                "win32_error_code": e.winerror,
                "service": service_name,
                "action": "start"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error starting service '{service_name}': {str(e)}",
                "service": service_name,
                "action": "start"
            }
    
    @staticmethod
    def stop_service(service_name: str, timeout: int = 30) -> Dict[str, Any]:
        """Stop a Windows service.
        
        Args:
            service_name: Name of the service to stop
            timeout: Maximum time to wait for the service to stop (in seconds)
            
        Returns:
            Dict with status information
        """
        try:
            # Check if service exists and get current status
            service = ServiceManager.get_service(service_name)
            if not service:
                return {
                    "success": False,
                    "error": f"Service '{service_name}' not found",
                    "service": service_name,
                    "action": "stop"
                }
            
            if service.status == ServiceStatus.STOPPED:
                return {
                    "success": True,
                    "message": f"Service '{service_name}' is already stopped",
                    "service": service_name,
                    "status": service.status.value,
                    "action": "stop"
                }
            
            # Stop the service
            start_time = time.time()
            win32serviceutil.StopService(service_name)
            
            # Wait for the service to stop
            while time.time() - start_time < timeout:
                service = ServiceManager.get_service(service_name)
                if not service:
                    return {
                        "success": False,
                        "error": f"Service '{service_name}' not found after stop attempt",
                        "service": service_name,
                        "action": "stop"
                    }
                
                if service.status == ServiceStatus.STOPPED:
                    return {
                        "success": True,
                        "message": f"Successfully stopped service '{service_name}'",
                        "service": service_name,
                        "status": service.status.value,
                        "elapsed_time": time.time() - start_time,
                        "action": "stop"
                    }
                
                time.sleep(0.5)
            
            # If we get here, the service didn't stop in time
            service = ServiceManager.get_service(service_name)
            return {
                "success": False,
                "error": f"Timeout waiting for service '{service_name}' to stop",
                "service": service_name,
                "status": service.status.value if service else "UNKNOWN",
                "elapsed_time": time.time() - start_time,
                "action": "stop"
            }
            
        except win32_error as e:
            error_msg = ServiceManager._get_win32_error_message(e)
            return {
                "success": False,
                "error": f"Failed to stop service '{service_name}': {error_msg}",
                "win32_error_code": e.winerror,
                "service": service_name,
                "action": "stop"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error stopping service '{service_name}': {str(e)}",
                "service": service_name,
                "action": "stop"
            }
    
    @staticmethod
    def restart_service(service_name: str, timeout: int = 60) -> Dict[str, Any]:
        """Restart a Windows service.
        
        Args:
            service_name: Name of the service to restart
            timeout: Maximum time to wait for the service to restart (in seconds)
            
        Returns:
            Dict with status information
        """
        # First stop the service
        stop_result = ServiceManager.stop_service(service_name, timeout // 2)
        if not stop_result["success"] and stop_result.get("status") != ServiceStatus.STOPPED.value:
            return {
                "success": False,
                "error": f"Failed to stop service during restart: {stop_result.get('error')}",
                "service": service_name,
                "action": "restart"
            }
        
        # Then start it again
        start_result = ServiceManager.start_service(service_name, timeout=timeout // 2)
        if not start_result["success"]:
            return {
                "success": False,
                "error": f"Failed to start service during restart: {start_result.get('error')}",
                "service": service_name,
                "action": "restart"
            }
        
        return {
            "success": True,
            "message": f"Successfully restarted service '{service_name}'",
            "service": service_name,
            "status": start_result.get("status", "UNKNOWN"),
            "pid": start_result.get("pid"),
            "elapsed_time": (stop_result.get("elapsed_time", 0) + 
                            start_result.get("elapsed_time", 0)),
            "action": "restart"
        }
    
    @staticmethod
    def set_startup_type(service_name: str, 
                        startup_type: Union[ServiceStartupType, str]) -> Dict[str, Any]:
        """Set the startup type for a service.
        
        Args:
            service_name: Name of the service
            startup_type: Desired startup type (AUTOMATIC, MANUAL, DISABLED, etc.)
            
        Returns:
            Dict with status information
        """
        try:
            # Convert string to enum if needed
            if isinstance(startup_type, str):
                startup_type = ServiceStartupType[startup_type.upper()]
            
            # Map our enum to Windows constants
            win32_startup_type = {
                ServiceStartupType.BOOT: win32service.SERVICE_BOOT_START,
                ServiceStartupType.SYSTEM: win32service.SERVICE_SYSTEM_START,
                ServiceStartupType.AUTOMATIC: win32service.SERVICE_AUTO_START,
                ServiceStartupType.MANUAL: win32service.SERVICE_DEMAND_START,
                ServiceStartupType.DISABLED: win32service.SERVICE_DISABLED,
            }.get(startup_type, win32service.SERVICE_DEMAND_START)
            
            # Open the service with configure access
            scm_handle = win32service.OpenSCManager(
                None, None, win32service.SC_MANAGER_CONNECT
            )
            
            try:
                service_handle = win32service.OpenService(
                    scm_handle,
                    service_name,
                    win32service.SERVICE_CHANGE_CONFIG
                )
                
                try:
                    # Change the service config
                    win32service.ChangeServiceConfig(
                        service_handle,
                        win32service.SERVICE_NO_CHANGE,  # service type
                        win32_startup_type,
                        win32service.SERVICE_NO_CHANGE,  # error control
                        None,  # binary path
                        None,  # load order group
                        None,  # dependencies
                        None,  # service start name
                        None,  # password
                        None,  # display name
                    )
                    
                    return {
                        "success": True,
                        "message": f"Set startup type for service '{service_name}' to {startup_type.value}",
                        "service": service_name,
                        "startup_type": startup_type.value,
                        "action": "set_startup_type"
                    }
                finally:
                    win32service.CloseServiceHandle(service_handle)
            finally:
                win32service.CloseServiceHandle(scm_handle)
                
        except win32_error as e:
            error_msg = ServiceManager._get_win32_error_message(e)
            return {
                "success": False,
                "error": f"Failed to set startup type for service '{service_name}': {error_msg}",
                "win32_error_code": e.winerror,
                "service": service_name,
                "action": "set_startup_type"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error setting startup type for service '{service_name}': {str(e)}",
                "service": service_name,
                "action": "set_startup_type"
            }
    
    @staticmethod
    def _get_win32_error_message(error: win32_error) -> str:
        """Get a human-readable error message from a win32 error."""
        try:
            # Try to get the system error message
            if hasattr(ctypes, 'FormatError'):
                return ctypes.FormatError(error.winerror).strip()
            
            # Fallback to known error codes
            error_messages = {
                winerror.ERROR_SERVICE_DOES_NOT_EXIST: "The specified service does not exist",
                winerror.ERROR_SERVICE_ALREADY_RUNNING: "The service is already running",
                winerror.ERROR_SERVICE_NOT_ACTIVE: "The service is not running",
                winerror.ERROR_ACCESS_DENIED: "Access is denied",
                winerror.ERROR_INVALID_HANDLE: "The handle is invalid",
                winerror.ERROR_PATH_NOT_FOUND: "The system cannot find the path specified",
                winerror.ERROR_SERVICE_DISABLED: "The service cannot be started because it is disabled",
                winerror.ERROR_SERVICE_LOGON_FAILED: "The service did not start due to a logon failure",
                winerror.ERROR_SERVICE_REQUEST_TIMEOUT: "The service did not respond to the start request in a timely fashion",
            }
            
            return error_messages.get(error.winerror, str(error))
        except Exception:
            return str(error)

@tool(
    name="list_services",
    description="List all Windows services with their status and details",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="status",
            type=str,
            description="Filter services by status (all, running, stopped, start_pending, stop_pending, paused, pause_pending, continue_pending)",
            default="all",
            required=False
        ),
        ToolParameter(
            name="startup_type",
            type=str,
            description="Filter services by startup type (all, automatic, manual, disabled, boot, system)",
            default="all",
            required=False
        ),
        ToolParameter(
            name="search",
            type=str,
            description="Search filter for service names or display names (case-insensitive)",
            default="",
            required=False
        ),
        ToolParameter(
            name="include_details",
            type=bool,
            description="Include detailed information about each service",
            default=True,
            required=False
        )
    ],
    return_type=Dict,
    return_description="Dictionary containing the list of services and their details"
)
class ListServicesTool(BaseTool):
    """Tool for listing Windows services."""
    
    async def execute(self, **kwargs) -> Dict:
        """List Windows services with optional filtering."""
        status_filter = kwargs.get("status", "all").lower()
        startup_type_filter = kwargs.get("startup_type", "all").lower()
        search_term = (kwargs.get("search", "") or "").lower()
        include_details = kwargs.get("include_details", True)
        
        try:
            # Get all services
            services = await asyncio.get_event_loop().run_in_executor(
                None, ServiceManager.get_services
            )
            
            filtered_services = []
            
            # Apply filters
            for service in services:
                # Status filter
                if status_filter != "all" and service.status.value.lower() != status_filter.upper():
                    continue
                
                # Startup type filter
                if startup_type_filter != "all" and \
                   service.startup_type.value.lower() != startup_type_filter.upper():
                    continue
                
                # Search filter
                if search_term and not (search_term in service.name.lower() or 
                                      search_term in (service.display_name or "").lower()):
                    continue
                
                # Convert to dict with or without details
                if include_details:
                    filtered_services.append(service.to_dict())
                else:
                    filtered_services.append({
                        "name": service.name,
                        "display_name": service.display_name,
                        "status": service.status.value,
                        "startup_type": service.startup_type.value,
                        "pid": service.pid
                    })
            
            return {
                "success": True,
                "count": len(filtered_services),
                "services": filtered_services,
                "filters": {
                    "status": status_filter,
                    "startup_type": startup_type_filter,
                    "search": search_term
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing services: {str(e)}",
                "count": 0,
                "services": []
            }

@tool(
    name="get_service",
    description="Get detailed information about a specific Windows service",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="service_name",
            type=str,
            description="Name of the service to get information about",
            required=True
        )
    ],
    return_type=Dict,
    return_description="Dictionary containing detailed information about the service"
)
class GetServiceTool(BaseTool):
    """Tool for getting detailed information about a Windows service."""
    
    async def execute(self, **kwargs) -> Dict:
        """Get information about a specific Windows service."""
        service_name = kwargs.get("service_name")
        if not service_name:
            return {
                "success": False,
                "error": "Service name is required"
            }
        
        try:
            service = await asyncio.get_event_loop().run_in_executor(
                None, ServiceManager.get_service, service_name
            )
            
            if not service:
                return {
                    "success": False,
                    "error": f"Service '{service_name}' not found"
                }
            
            return {
                "success": True,
                "service": service.to_dict()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting service '{service_name}': {str(e)}",
                "service_name": service_name
            }

@tool(
    name="start_service",
    description="Start a Windows service",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="service_name",
            type=str,
            description="Name of the service to start",
            required=True
        ),
        ToolParameter(
            name="args",
            type=list,
            description="Optional arguments to pass to the service",
            default=[],
            required=False
        ),
        ToolParameter(
            name="timeout",
            type=int,
            description="Maximum time to wait for the service to start (in seconds)",
            default=30,
            required=False
        )
    ],
    return_type=Dict,
    return_description="Dictionary containing the result of the start operation"
)
class StartServiceTool(BaseTool):
    """Tool for starting a Windows service."""
    
    async def execute(self, **kwargs) -> Dict:
        """Start a Windows service."""
        service_name = kwargs.get("service_name")
        args = kwargs.get("args", [])
        timeout = kwargs.get("timeout", 30)
        
        if not service_name:
            return {
                "success": False,
                "error": "Service name is required"
            }
        
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, ServiceManager.start_service, service_name, args, timeout
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Error starting service '{service_name}': {str(e)}",
                "service_name": service_name
            }

@tool(
    name="stop_service",
    description="Stop a Windows service",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="service_name",
            type=str,
            description="Name of the service to stop",
            required=True
        ),
        ToolParameter(
            name="timeout",
            type=int,
            description="Maximum time to wait for the service to stop (in seconds)",
            default=30,
            required=False
        )
    ],
    return_type=Dict,
    return_description="Dictionary containing the result of the stop operation"
)
class StopServiceTool(BaseTool):
    """Tool for stopping a Windows service."""
    
    async def execute(self, **kwargs) -> Dict:
        """Stop a Windows service."""
        service_name = kwargs.get("service_name")
        timeout = kwargs.get("timeout", 30)
        
        if not service_name:
            return {
                "success": False,
                "error": "Service name is required"
            }
        
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, ServiceManager.stop_service, service_name, timeout
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Error stopping service '{service_name}': {str(e)}",
                "service_name": service_name
            }

@tool(
    name="restart_service",
    description="Restart a Windows service",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="service_name",
            type=str,
            description="Name of the service to restart",
            required=True
        ),
        ToolParameter(
            name="timeout",
            type=int,
            description="Maximum time to wait for the service to restart (in seconds)",
            default=60,
            required=False
        )
    ],
    return_type=Dict,
    return_description="Dictionary containing the result of the restart operation"
)
class RestartServiceTool(BaseTool):
    """Tool for restarting a Windows service."""
    
    async def execute(self, **kwargs) -> Dict:
        """Restart a Windows service."""
        service_name = kwargs.get("service_name")
        timeout = kwargs.get("timeout", 60)
        
        if not service_name:
            return {
                "success": False,
                "error": "Service name is required"
            }
        
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, ServiceManager.restart_service, service_name, timeout
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Error restarting service '{service_name}': {str(e)}",
                "service_name": service_name
            }

@tool(
    name="set_service_startup_type",
    description="Set the startup type for a Windows service",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="service_name",
            type=str,
            description="Name of the service",
            required=True
        ),
        ToolParameter(
            name="startup_type",
            type=str,
            description="Desired startup type (automatic, manual, disabled, boot, system)",
            required=True,
            choices=[t.value.lower() for t in ServiceStartupType]
        )
    ],
    return_type=Dict,
    return_description="Dictionary containing the result of the operation"
)
class SetServiceStartupTypeTool(BaseTool):
    """Tool for setting the startup type of a Windows service."""
    
    async def execute(self, **kwargs) -> Dict:
        """Set the startup type for a Windows service."""
        service_name = kwargs.get("service_name")
        startup_type = kwargs.get("startup_type")
        
        if not service_name:
            return {
                "success": False,
                "error": "Service name is required"
            }
        
        if not startup_type:
            return {
                "success": False,
                "error": "Startup type is required"
            }
        
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, ServiceManager.set_startup_type, service_name, startup_type
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Error setting startup type for service '{service_name}': {str(e)}",
                "service_name": service_name,
                "startup_type": startup_type
            }

@tool(
    name="get_service_logs",
    description="Get event logs for a Windows service",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="service_name",
            type=str,
            description="Name of the service to get logs for",
            required=True
        ),
        ToolParameter(
            name="log_type",
            type=str,
            description="Type of logs to retrieve (system, application, security, setup, forwardedevents, or application and services logs path)",
            default="system",
            required=False
        ),
        ToolParameter(
            name="source",
            type=str,
            description="Event source to filter by (defaults to service name if not specified)",
            default="",
            required=False
        ),
        ToolParameter(
            name="last",
            type=str,
            description="Get logs from the last X minutes/hours/days (e.g., '10m', '2h', '1d')",
            default="1h",
            required=False
        ),
        ToolParameter(
            name="limit",
            type=int,
            description="Maximum number of log entries to return",
            default=50,
            required=False
        ),
        ToolParameter(
            name="event_level",
            type=str,
            description="Filter by event level (all, critical, error, warning, information, verbose)",
            default="all",
            required=False,
            choices=["all", "critical", "error", "warning", "information", "verbose"]
        )
    ],
    return_type=Dict,
    return_description="Dictionary containing the service logs"
)
class GetServiceLogsTool(BaseTool):
    """Tool for retrieving Windows event logs for a service."""
    
    async def execute(self, **kwargs) -> Dict:
        """Get event logs for a Windows service."""
        import win32evtlog
        import win32con
        import win32api
        from datetime import datetime, timedelta
        import re
        
        service_name = kwargs.get("service_name")
        log_type = kwargs.get("log_type", "system")
        source = kwargs.get("source", service_name)
        last = kwargs.get("last", "1h")
        limit = kwargs.get("limit", 50)
        event_level = kwargs.get("event_level", "all").lower()
        
        if not service_name:
            return {
                "success": False,
                "error": "Service name is required"
            }
        
        # Map event level to Windows event levels
        level_map = {
            "critical": win32con.EVENTLOG_ERROR_TYPE,
            "error": win32con.EVENTLOG_ERROR_TYPE,
            "warning": win32con.EVENTLOG_WARNING_TYPE,
            "information": win32con.EVENTLOG_INFORMATION_TYPE,
            "verbose": win32con.EVENTLOG_AUDIT_SUCCESS  # Not exact, but works for filtering
        }
        
        try:
            # Calculate time filter
            now = datetime.now()
            time_ago = now
            
            # Parse time string (e.g., '10m', '2h', '1d')
            time_match = re.match(r'^(\d+)([mhd])$', last.lower())
            if time_match:
                num = int(time_match.group(1))
                unit = time_match.group(2)
                
                if unit == 'm':
                    time_ago = now - timedelta(minutes=num)
                elif unit == 'h':
                    time_ago = now - timedelta(hours=num)
                elif unit == 'd':
                    time_ago = now - timedelta(days=num)
            
            # Convert to Windows filetime
            time_ago_ft = win32api.GetTimeFormat() - int((now - time_ago).total_seconds() * 10000000)
            
            # Open the event log
            try:
                hand = win32evtlog.OpenEventLog(None, log_type)
            except Exception:
                # Try with Application log if the specified log type fails
                try:
                    hand = win32evtlog.OpenEventLog(None, "Application")
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Could not open event log: {str(e)}",
                        "service_name": service_name,
                        "log_type": log_type
                    }
            
            # Set up flags for reading the log
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            # Prepare results
            logs = []
            total_events = 0
            
            try:
                while len(logs) < limit:
                    # Read events in chunks
                    events = win32evtlog.ReadEventLog(hand, flags, 0)
                    if not events:
                        break
                    
                    for event in events:
                        # Filter by time
                        if event.TimeGenerated.timestamp() < time_ago.timestamp():
                            continue
                        
                        # Filter by source if specified
                        event_source = getattr(event, 'SourceName', '')
                        if source and event_source.lower() != source.lower():
                            continue
                        
                        # Filter by level if specified
                        if event_level != "all":
                            if event_level == "critical" and event.EventType != win32con.EVENTLOG_ERROR_TYPE:
                                continue
                            if event_level == "error" and event.EventType != win32con.EVENTLOG_ERROR_TYPE:
                                continue
                            if event_level == "warning" and event.EventType != win32con.EVENTLOG_WARNING_TYPE:
                                continue
                            if event_level == "information" and event.EventType != win32con.EVENTLOG_INFORMATION_TYPE:
                                continue
                            if event_level == "verbose" and event.EventType not in [win32con.EVENTLOG_AUDIT_SUCCESS, win32con.EVENTLOG_AUDIT_FAILURE]:
                                continue
                        
                        # Format the log entry
                        log_entry = {
                            "timestamp": event.TimeGenerated.isoformat(),
                            "source": event_source,
                            "event_id": event.EventID & 0xFFFF,  # Lower 16 bits
                            "event_type": self._get_event_type(event.EventType),
                            "computer": event.ComputerName,
                            "message": self._get_event_message(event),
                            "data": event.StringInserts
                        }
                        
                        logs.append(log_entry)
                        total_events += 1
                        
                        if len(logs) >= limit:
                            break
                
                return {
                    "success": True,
                    "count": len(logs),
                    "total_events": total_events,
                    "service_name": service_name,
                    "log_type": log_type,
                    "logs": logs
                }
                
            finally:
                win32evtlog.CloseEventLog(hand)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error retrieving logs for service '{service_name}': {str(e)}",
                "service_name": service_name
            }
    
    def _get_event_type(self, event_type: int) -> str:
        """Convert Windows event type to string."""
        event_types = {
            0x0001: "Error",
            0x0010: "Audit Failure",
            0x0008: "Audit Success",
            0x0004: "Information",
            0x0002: "Warning"
        }
        return event_types.get(event_type, f"Unknown ({event_type})")
    
    def _get_event_message(self, event) -> str:
        """Get the message from a Windows event."""
        try:
            # Try to get the formatted message
            if hasattr(event, 'StringInserts') and event.StringInserts:
                return " ".join(str(x) for x in event.StringInserts if x)
            return "No message available"
        except Exception:
            return "Error retrieving message"
