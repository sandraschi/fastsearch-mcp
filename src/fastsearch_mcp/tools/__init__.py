"""
FastSearch MCP Tools - FastMCP 2.13 compliant tool implementations.

This module provides all the tools available in the FastSearch MCP server,
organized according to FastMCP 2.13 patterns and conventions.
"""

from .base import BaseTool
from .disk_analyzer import DiskAnalyzerTool
from .duplicate_finder import DuplicateFileFinderTool
from .file_search import FileContentSearchTool
from .help import HelpTool
from .integrity_checker import FileIntegrityCheckerTool
from .resource_monitor import SystemResourceMonitorTool
from .service_manager import (
    GetServiceLogsTool,
    GetServiceTool,
    ListServicesTool,
    RestartServiceTool,
    SetServiceStartupTypeTool,
    StartServiceTool,
    StopServiceTool,
)
from .service_status import ServiceStatusTool

# Tool registry for FastMCP 2.13
__all__ = [
    "BaseTool",
    "FileContentSearchTool",
    "DiskAnalyzerTool",
    "DuplicateFileFinderTool",
    "FileIntegrityCheckerTool",
    "SystemResourceMonitorTool",
    "ServiceStatusTool",
    "ListServicesTool",
    "GetServiceTool",
    "StartServiceTool",
    "StopServiceTool",
    "RestartServiceTool",
    "SetServiceStartupTypeTool",
    "GetServiceLogsTool",
    "HelpTool",
]

# All available tools
AVAILABLE_TOOLS = [
    FileContentSearchTool,
    DiskAnalyzerTool,
    DuplicateFileFinderTool,
    FileIntegrityCheckerTool,
    SystemResourceMonitorTool,
    ServiceStatusTool,
    ListServicesTool,
    GetServiceTool,
    StartServiceTool,
    StopServiceTool,
    RestartServiceTool,
    SetServiceStartupTypeTool,
    GetServiceLogsTool,
    HelpTool,
]
