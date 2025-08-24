"""
FastSearch MCP Bridge - Python implementation of the MCP 2.11.3 protocol.

This package provides a Python implementation of the Model-Controller-Presenter (MCP) 2.11.3 protocol
for the FastSearch NTFS search service. It includes a server implementation, tool registration system,
and various utilities for building MCP-compliant services.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union

# Set up basic logging first to capture any import-time issues
try:
    from .logging_config import get_logger, setup_logging
    
    # Set up basic console logging with default settings
    setup_logging(
        log_level=os.environ.get('FASTSEARCH_LOG_LEVEL', 'INFO'),
        console=True
    )
    logger = get_logger(__name__)
    
except Exception as e:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning("Failed to initialize logging: %s", e, exc_info=True)

# Now import other modules
try:
    from .mcp_server import McpServer
    from .ipc import IpcError
    from .exceptions import McpError
    from .tools import ToolRegistry, tool, ToolInfo
    from .logging_config import struct_message
    
    # Create a global registry instance
    _global_registry = ToolRegistry()
    
    def get_global_registry() -> ToolRegistry:
        """Get the global tool registry."""
        return _global_registry
    
    def register_tool(func) -> None:
        """Register a function as a tool in the global registry."""
        _global_registry.register(func)
        return func
        
    # Import tools to ensure they're registered
    try:
        from .tools.file_search import FileContentSearchTool  # noqa
        from .tools.disk_analyzer import DiskAnalyzerTool  # noqa
        from .tools.duplicate_finder import DuplicateFileFinderTool  # noqa
        from .tools.resource_monitor import SystemResourceMonitorTool, ProcessInfoTool  # noqa
        from .tools.integrity_checker import FileIntegrityCheckerTool, FileHasherTool  # noqa
        from .tools.service_manager import (  # noqa
            ListServicesTool, GetServiceTool, StartServiceTool, 
            StopServiceTool, RestartServiceTool, SetServiceStartupTypeTool,
            GetServiceLogsTool, ServiceManager, ServiceInfo, ServiceStatus, 
            ServiceStartupType
        )
        
        __all__ = [
            # Tool classes
            'FileContentSearchTool',
            'DiskAnalyzerTool',
            'DuplicateFileFinderTool',
            'SystemResourceMonitorTool',
            'ProcessInfoTool',
            'FileIntegrityCheckerTool',
            'FileHasherTool',
            
            # Service management tools
            'ListServicesTool',
            'GetServiceTool',
            'StartServiceTool',
            'StopServiceTool',
            'RestartServiceTool',
            'SetServiceStartupTypeTool',
            'GetServiceLogsTool',
            'ServiceManager',
            'ServiceInfo',
            'ServiceStatus',
            'ServiceStartupType',
            
            # Core classes
            'McpServer',
            'IpcError',
            'McpError',
            'ToolRegistry',
            'tool',
            'ToolInfo',
            'get_global_registry',
            'register_tool',
            'struct_message'
        ]
    except ImportError as e:
        logger.warning("Failed to import some tools: %s", e)
    
    # Import and register all built-in tools
    from .tools.help import help  # noqa
    
    # Import and register service management tools
    try:
        from .tools.service import register_tools as register_service_tools
        register_service_tools(_global_registry)
    except ImportError as e:
        logger.warning("Could not register service tools: %s", e)
    
    # Import and register NTFS health check tools
    try:
        from .tools.ntfs import register_tools as register_ntfs_tools
        register_ntfs_tools(_global_registry)
    except ImportError as e:
        logger.warning("Could not register NTFS tools: %s", e)
    
    # Log successful initialization
    logger.info("FastSearch MCP Bridge initialized (version: %s)", __version__)
    
except Exception as e:
    logger.error("Failed to initialize FastSearch MCP Bridge: %s", e, exc_info=True)
    raise

__version__ = "0.4.0"
__all__ = [
    "McpServer", 
    "IpcError", 
    "McpError",
    "ToolRegistry",
    "ToolInfo",
    "tool",
    "register_tool",
    "get_global_registry",
    "get_logger",
    "setup_logging",
    "struct_message"
]
