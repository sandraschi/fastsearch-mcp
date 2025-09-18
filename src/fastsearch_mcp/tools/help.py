"""
Help system for FastSearch MCP Tools.

Provides documentation and usage information for all registered tools.
"""
from typing import Dict, List, Any
from .base import BaseTool, ToolCategory, ToolParameter, tool


@tool(
    name="help",
    description="Get help for available tools",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="tool_name",
            type=str,
            description="Optional name of a specific tool to get help for",
            required=False
        )
    ],
    return_type=Dict[str, Any],
    return_description="Dictionary containing tool documentation"
)
class HelpTool(BaseTool):
    """Help tool for FastSearch MCP."""
    
    async def execute(self, tool_name: str = None) -> Dict[str, Any]:
        """
        Get help for tools.
        
        Args:
            tool_name: Optional name of a specific tool to get help for
            
        Returns:
            Dictionary containing tool documentation
        """
        if tool_name:
            return await self._get_tool_help(tool_name)
        else:
            return await self._list_all_tools()
    
    async def _list_all_tools(self) -> Dict[str, Any]:
        """List all available tools."""
        return {
            "message": "FastSearch MCP Tools",
            "tools": [
                "file_content_search - Search for text patterns in files",
                "disk_analyzer - Analyze disk usage and file distribution", 
                "duplicate_finder - Find duplicate files",
                "integrity_checker - Check file integrity and hashes",
                "resource_monitor - Monitor system resources",
                "service_manager - Manage Windows services",
                "help - Get help for tools"
            ]
        }
    
    async def _get_tool_help(self, tool_name: str) -> Dict[str, Any]:
        """Get help for a specific tool."""
        help_text = {
            "file_content_search": "Search for text patterns in files using regex",
            "disk_analyzer": "Analyze disk usage and file distribution patterns",
            "duplicate_finder": "Find duplicate files by content hash",
            "integrity_checker": "Check file integrity using various hash algorithms",
            "resource_monitor": "Monitor CPU, memory, and disk usage",
            "service_manager": "Manage Windows services (start, stop, restart)",
            "help": "Get help for available tools"
        }
        
        return {
            "tool": tool_name,
            "help": help_text.get(tool_name, "Unknown tool")
        }