"""Service status tool for FastSearch MCP.

This tool provides multilevel status information about the FastSearch C++ service,
including whether it's running, installed, and can be connected to.
Supports basic, intermediate, and advanced detail levels.
"""

from typing import Any

from fastsearch_mcp.logging_config import get_logger
from fastsearch_mcp.mcp_instance import mcp
from fastsearch_mcp.service_client import (
    SERVICE_EXECUTABLE,
    SERVICE_NAME,
)
from fastsearch_mcp.service_client import (
    get_service_status as get_service_status_impl,
)

logger = get_logger(__name__)


@mcp.tool
async def service_status(level: str = "basic") -> dict[str, Any]:
    """Get the current status of the FastSearch C++ service with multilevel detail support.

    Provides basic, intermediate, or advanced status information about the service,
    including whether it's running, installed, and can be connected to via named pipe.

    Args:
        level: Detail level: basic (quick status), intermediate (detailed info),
            advanced (comprehensive with diagnostics)

    Returns:
        Dictionary containing service status information at the specified detail level
    """
    try:
        status = await get_service_status_impl()

        if level == "basic":
            return {
                "success": True,
                "level": level,
                "running": status.get("running", False),
                "service_state": status.get("service_state", "UNKNOWN"),
                "pipe_connected": status.get("pipe_connected", False),
            }
        elif level == "intermediate":
            return {
                "success": True,
                "level": level,
                "running": status.get("running", False),
                "service_state": status.get("service_state", "UNKNOWN"),
                "executable_path": status.get("executable_path"),
                "pipe_name": status.get("pipe_name"),
                "pipe_connected": status.get("pipe_connected", False),
                "pipe_info": status.get("pipe_info"),
            }
        else:  # advanced
            # Get additional diagnostic information
            executable_exists = SERVICE_EXECUTABLE.exists() if SERVICE_EXECUTABLE else False
            executable_size = None
            executable_modified = None

            if executable_exists:
                try:
                    stat = SERVICE_EXECUTABLE.stat()
                    executable_size = stat.st_size
                    executable_modified = stat.st_mtime
                except Exception:
                    pass

            return {
                "success": True,
                "level": level,
                "running": status.get("running", False),
                "service_state": status.get("service_state", "UNKNOWN"),
                "service_name": SERVICE_NAME,
                "executable_path": status.get("executable_path"),
                "executable_exists": executable_exists,
                "executable_size": executable_size,
                "executable_modified": executable_modified,
                "pipe_name": status.get("pipe_name"),
                "pipe_connected": status.get("pipe_connected", False),
                "pipe_info": status.get("pipe_info"),
                "error": status.get("error"),
                "diagnostics": {
                    "executable_accessible": executable_exists,
                    "pipe_available": status.get("pipe_connected", False),
                    "service_registered": status.get("service_state") != "UNKNOWN"
                    if status.get("service_state")
                    else False,
                },
            }
    except Exception as e:
        logger.error(f"Error getting service status: {e}", exc_info=True)
        error_result = {"success": False, "level": level, "error": str(e), "running": False}

        if level == "advanced":
            error_result["diagnostics"] = {
                "executable_accessible": SERVICE_EXECUTABLE.exists() if SERVICE_EXECUTABLE else False,
                "error_type": type(e).__name__,
            }

        return error_result
