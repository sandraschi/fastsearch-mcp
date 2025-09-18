"""
FastSearch MCP Tools - FastMCP 2.12 compliant tool implementations.

This module provides all the tools available in the FastSearch MCP server,
organized according to FastMCP 2.12 patterns and conventions.
"""

from .base import BaseTool
from .file_search import FileContentSearchTool
from .disk_analyzer import DiskAnalyzerTool
from .duplicate_finder import DuplicateFileFinderTool
from .integrity_checker import FileIntegrityCheckerTool
from .resource_monitor import SystemResourceMonitorTool
from .service_manager import (
    ListServicesTool,
    GetServiceTool,
    StartServiceTool,
    StopServiceTool,
    RestartServiceTool,
    SetServiceStartupTypeTool,
    GetServiceLogsTool,
)
from .help import HelpTool

# Tool registry for FastMCP 2.12
__all__ = [
    "BaseTool",
    "FileContentSearchTool", 
    "DiskAnalyzerTool",
    "DuplicateFileFinderTool",
    "FileIntegrityCheckerTool",
    "SystemResourceMonitorTool",
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
    ListServicesTool,
    GetServiceTool,
    StartServiceTool,
    StopServiceTool,
    RestartServiceTool,
    SetServiceStartupTypeTool,
    GetServiceLogsTool,
    HelpTool,
]