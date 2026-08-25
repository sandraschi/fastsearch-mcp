"""
Service management tools for FastSearch MCP.

This module provides tools for managing the FastSearch service on Windows,
including starting, stopping, and checking the status of the service.
"""

import ctypes
import sys
import winreg
from pathlib import Path

import win32service
import win32serviceutil
import winerror

from ..exceptions import McpError
from ..logging_config import get_logger
from ..mcp_instance import mcp

logger = get_logger(__name__)

# Constants
SERVICE_NAME = "FastSearchMCP"  # Must match service_client.py
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
    except OSError:
        pass

    # Fall back to default location
    return Path(sys.executable).parent / "fastsearch-service.exe"


@mcp.tool
async def service_status_fastsearch() -> dict[str, str | bool | int]:
    """Get the status of the FastSearch service.

    Returns:
        Dictionary containing service status information with 'installed' field
        indicating whether the service exists, and 'status' indicating current state
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
            win32service.SERVICE_PAUSED: "paused",
        }

        # QueryServiceStatus returns (serviceType, currentState, controlsAccepted,
        # win32ExitCode, serviceSpecificExitCode, checkPoint, waitHint)
        # For PID, we need to use QueryServiceStatusEx
        current_state = status[1]
        current_status = status_codes.get(current_state, "unknown")

        # Get PID if service is running
        pid = None
        if current_state == win32service.SERVICE_RUNNING:
            try:
                # Use QueryServiceStatusEx to get process ID
                scm_handle = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
                try:
                    service_handle = win32service.OpenService(
                        scm_handle, SERVICE_NAME, win32service.SERVICE_QUERY_STATUS
                    )
                    try:
                        status_ex = win32service.QueryServiceStatusEx(service_handle)
                        pid = status_ex.get("ProcessId") if isinstance(status_ex, dict) else None
                    finally:
                        win32service.CloseServiceHandle(service_handle)
                finally:
                    win32service.CloseServiceHandle(scm_handle)
            except Exception:
                pass  # PID not critical, continue without it

        return {
            "status": current_status,
            "installed": True,  # Service exists
            "pid": pid,
            "can_control": _is_admin(),
        }
    except Exception as e:
        if hasattr(e, "winerror") and e.winerror == winerror.ERROR_SERVICE_DOES_NOT_EXIST:
            return {"status": "not_installed", "installed": False, "can_install": _is_admin()}
        raise ServiceError(f"Failed to get service status: {e}") from e


@mcp.tool
async def service_start_fastsearch(dry_run: bool = False) -> dict[str, str | bool]:
    """SERVICE_START_FASTSEARCH - Start the FastSearch NTFS indexing Windows service.

    Requires local **Administrator** (elevated). Use ``service_status`` first to see
    whether the service is installed and running. This is narrower than generic
    ``start_service`` (disabled in default builds): it only targets ``FastSearchMCP``.

    Args:
        dry_run: If True, does not call SCM; returns whether the caller is admin and the
            target service name (use before mutating).

    Returns:
        ``success`` True and ``message`` on OK; raises ``ServiceError`` on failure or
        non-admin (unless ``dry_run``).

    Recovery: Not installed → install flow; access denied → elevate shell; already running
    is typically a no-op at SCM level-check ``service_status``.
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "service": SERVICE_NAME,
            "is_admin": _is_admin(),
            "message": f"Would start {SERVICE_NAME} (admin={_is_admin()})",
        }

    if not _is_admin():
        raise ServiceError("Administrator privileges are required to start the service")

    try:
        win32serviceutil.StartService(SERVICE_NAME)
        return {"success": True, "message": "Service started successfully"}
    except Exception as e:
        raise ServiceError(f"Failed to start service: {e}") from e


@mcp.tool
async def service_stop_fastsearch(dry_run: bool = False) -> dict[str, str | bool]:
    """SERVICE_STOP_FASTSEARCH - Stop the FastSearch indexing service (admin).

    Stopping the service pauses background indexing until started again; active MCP
    clients may lose connectivity to the local indexer depending on deployment.

    Args:
        dry_run: If True, reports admin capability without stopping.

    Returns:
        ``success`` True on stop; ``ServiceError`` on failure.

    Recovery: In use → retry after closing consumers; access denied → elevate.
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "service": SERVICE_NAME,
            "is_admin": _is_admin(),
            "message": f"Would stop {SERVICE_NAME} (admin={_is_admin()})",
        }

    if not _is_admin():
        raise ServiceError("Administrator privileges are required to stop the service")

    try:
        win32serviceutil.StopService(SERVICE_NAME)
        return {"success": True, "message": "Service stopped successfully"}
    except Exception as e:
        raise ServiceError(f"Failed to stop service: {e}") from e


@mcp.tool
async def service_restart_fastsearch(dry_run: bool = False) -> dict[str, str | bool]:
    """SERVICE_RESTART_FASTSEARCH - Restart FastSearch (single SCM restart call; admin).

    Equivalent to a stop+start from the perspective of dependent apps; brief outage while
    the process recycles.

    Args:
        dry_run: If True, reports admin capability without restarting.

    Returns:
        ``success`` True on restart; ``ServiceError`` on failure.

    Recovery: Same as stop/start; verify ``service_status`` after errors.
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "service": SERVICE_NAME,
            "is_admin": _is_admin(),
            "message": f"Would restart {SERVICE_NAME} (admin={_is_admin()})",
        }

    if not _is_admin():
        raise ServiceError("Administrator privileges are required to restart the service")

    try:
        win32serviceutil.RestartService(SERVICE_NAME)
        return {"success": True, "message": "Service restarted successfully"}
    except Exception as e:
        raise ServiceError(f"Failed to restart service: {e}") from e


@mcp.tool
async def service_install_fastsearch(
    executable_path: str | None = None, auto_start: bool = True
) -> dict[str, str | bool]:
    """Install the FastSearch service.

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
            exeArgs="run",
        )

        # Set service description
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                f"SYSTEM\\CurrentControlSet\\Services\\{SERVICE_NAME}",
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(key, "Description", 0, winreg.REG_SZ, SERVICE_DESCRIPTION)
        except Exception as e:
            logger.warning(f"Failed to set service description: {e}")

        if auto_start:
            win32serviceutil.StartService(SERVICE_NAME)

        return {
            "success": True,
            "message": f"Service installed successfully{' and started' if auto_start else ''}",
            "executable": executable_path,
        }
    except Exception as e:
        raise ServiceError(f"Failed to install service: {e}") from e


@mcp.tool
async def service_uninstall_fastsearch() -> dict[str, str | bool]:
    """Uninstall the FastSearch service.

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
        raise ServiceError(f"Failed to uninstall service: {e}") from e


@mcp.tool
async def service_repair_fastsearch() -> dict[str, str | bool]:
    """Repair the FastSearch service installation.

    This will reinstall the service with default settings.

    Returns:
        Dictionary with operation result
    """
    if not _is_admin():
        raise ServiceError("Administrator privileges are required to repair the service")

    try:
        # Check if service exists
        try:
            win32serviceutil.QueryServiceStatus(SERVICE_NAME)
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
        return await service_install_fastsearch()
    except Exception as e:
        raise ServiceError(f"Failed to repair service: {e}") from e


# Tools are registered via @mcp.tool decorator when imported
