"""
Service status tool for FastSearch MCP.

This tool provides multilevel status information about the FastSearch C++ service,
including whether it's running, installed, and can be connected to.
Supports basic, intermediate, and advanced detail levels.
"""

from typing import Any, Dict

from fastsearch_mcp.logging_config import get_logger
from fastsearch_mcp.service_client import (
    SERVICE_EXECUTABLE,
    SERVICE_NAME,
)
from fastsearch_mcp.service_client import (
    get_service_status as get_service_status_impl,
)
from fastsearch_mcp.tools.base import BaseTool, ToolCategory, ToolParameter, tool

logger = get_logger(__name__)


@tool(
    name="service_status",
    description="Get the current status of the FastSearch C++ service with multilevel detail support (basic, intermediate, advanced)",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="level",
            type=str,
            description="Detail level: basic (quick status), intermediate (detailed info), advanced (comprehensive with diagnostics)",
            required=False,
            default="basic",
            choices=["basic", "intermediate", "advanced"],
        )
    ],
    return_type=Dict,
    return_description="Dictionary containing service status information at the specified detail level",
)
class ServiceStatusTool(BaseTool):
    """Multilevel service status tool for FastSearch MCP."""

    async def execute(self, level: str = "basic", **kwargs) -> Dict[str, Any]:
        """Get the current status of the FastSearch C++ service with multilevel detail.

        Args:
            level: Detail level (basic, intermediate, advanced)

        Returns:
            Dictionary containing service status information at the specified level
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
                    "executable_accessible": SERVICE_EXECUTABLE.exists()
                    if SERVICE_EXECUTABLE
                    else False,
                    "error_type": type(e).__name__,
                }

            return error_result
