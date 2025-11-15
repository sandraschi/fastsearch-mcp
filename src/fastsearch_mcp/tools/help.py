"""
Help system for FastSearch MCP Tools.

Provides multilevel documentation and usage information for all registered tools.
Supports basic, intermediate, and advanced detail levels.
"""

from typing import Any, Dict

from .base import BaseTool, ToolCategory, ToolParameter, tool


@tool(
    name="help",
    description="Get help for available tools with multilevel detail support (basic, intermediate, advanced)",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="tool_name",
            type=str,
            description="Optional name of a specific tool to get help for",
            required=False,
        ),
        ToolParameter(
            name="level",
            type=str,
            description="Detail level: basic (quick overview), intermediate (detailed), advanced (comprehensive with examples)",
            required=False,
            default="basic",
            choices=["basic", "intermediate", "advanced"],
        ),
    ],
    return_type=Dict[str, Any],
    return_description="Dictionary containing tool documentation at the specified detail level",
)
class HelpTool(BaseTool):
    """Multilevel help tool for FastSearch MCP."""

    async def execute(self, tool_name: str = None, level: str = "basic") -> Dict[str, Any]:
        """
        Get help for tools with multilevel detail support.

        Args:
            tool_name: Optional name of a specific tool to get help for
            level: Detail level (basic, intermediate, advanced)

        Returns:
            Dictionary containing tool documentation at the specified level
        """
        if tool_name:
            return await self._get_tool_help(tool_name, level)
        else:
            return await self._list_all_tools(level)

    async def _list_all_tools(self, level: str) -> Dict[str, Any]:
        """List all available tools with appropriate detail level."""
        # Get tools from registry to avoid circular import
        from . import AVAILABLE_TOOLS

        tools = []
        for tool_class in AVAILABLE_TOOLS:
            try:
                tool_def = tool_class.get_definition()
                if level == "basic":
                    tools.append(f"{tool_def.name} - {tool_def.description[:60]}...")
                elif level == "intermediate":
                    tools.append(
                        {
                            "name": tool_def.name,
                            "description": tool_def.description,
                            "category": tool_def.category.value,
                            "parameters": len(tool_def.parameters),
                        }
                    )
                else:  # advanced
                    tools.append(
                        {
                            "name": tool_def.name,
                            "description": tool_def.description,
                            "category": tool_def.category.value,
                            "parameters": [p.to_dict() for p in tool_def.parameters],
                            "return_type": tool_def.return_type.__name__,
                            "return_description": tool_def.return_description,
                            "requires_elevation": tool_def.requires_elevation,
                        }
                    )
            except Exception:
                continue

        result = {
            "message": "FastSearch MCP Tools",
            "level": level,
            "count": len(tools),
            "tools": tools,
        }

        if level == "advanced":
            result["categories"] = {
                cat.value: [t["name"] for t in tools if t["category"] == cat.value]
                for cat in ToolCategory
            }

        return result

    async def _get_tool_help(self, tool_name: str, level: str) -> Dict[str, Any]:
        """Get help for a specific tool with multilevel detail."""
        # Get tools from registry to avoid circular import
        from . import AVAILABLE_TOOLS

        # Find the tool
        tool_class = None
        for tc in AVAILABLE_TOOLS:
            try:
                tool_def = tc.get_definition()
                if tool_def.name == tool_name:
                    tool_class = tc
                    break
            except Exception:
                continue

        if not tool_class:
            return {
                "tool": tool_name,
                "level": level,
                "error": "Tool not found",
                "available_tools": [
                    tc.get_definition().name
                    for tc in AVAILABLE_TOOLS
                    if hasattr(tc, "get_definition")
                ],
            }

        tool_def = tool_class.get_definition()

        if level == "basic":
            return {
                "tool": tool_name,
                "level": level,
                "description": tool_def.description,
                "category": tool_def.category.value,
            }
        elif level == "intermediate":
            return {
                "tool": tool_name,
                "level": level,
                "description": tool_def.description,
                "category": tool_def.category.value,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type.__name__,
                        "description": p.description,
                        "required": p.required,
                    }
                    for p in tool_def.parameters
                ],
                "returns": {
                    "type": tool_def.return_type.__name__,
                    "description": tool_def.return_description,
                },
            }
        else:  # advanced
            return {
                "tool": tool_name,
                "level": level,
                "description": tool_def.description,
                "category": tool_def.category.value,
                "parameters": [p.to_dict() for p in tool_def.parameters],
                "returns": {
                    "type": tool_def.return_type.__name__,
                    "description": tool_def.return_description,
                },
                "requires_elevation": tool_def.requires_elevation,
                "tags": list(tool_def.tags) if tool_def.tags else [],
                "enabled": tool_def.enabled,
                "examples": self._get_examples(tool_name),
            }

    def _get_examples(self, tool_name: str) -> list:
        """Get usage examples for a tool."""
        examples = {
            "service_status": [
                {
                    "description": "Get basic service status",
                    "call": {"tool_name": "service_status", "arguments": {}},
                }
            ],
            "file_content_search": [
                {
                    "description": "Search for Python files containing 'import'",
                    "call": {
                        "tool_name": "file_content_search",
                        "arguments": {
                            "search_pattern": "import",
                            "search_dir": "C:\\Dev",
                            "file_pattern": "*.py",
                            "max_results": 10,
                        },
                    },
                }
            ],
            "disk_analyzer": [
                {
                    "description": "Analyze C: drive usage",
                    "call": {
                        "tool_name": "analyze_disk_usage",
                        "arguments": {"path": "C:\\", "max_depth": 3, "find_largest": True},
                    },
                }
            ],
        }
        return examples.get(tool_name, [])
