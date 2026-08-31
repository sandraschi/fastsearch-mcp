"""
Help system for FastSearch MCP Tools.

Provides multilevel documentation and usage information for all registered tools.
Supports basic, intermediate, and advanced detail levels.
"""

import inspect
import logging
from typing import Any

from fastsearch_mcp.mcp_instance import mcp

logger = logging.getLogger(__name__)


@mcp.tool
async def help(tool_name: str | None = None, level: str = "basic") -> dict[str, Any]:
    """Get help for available tools with multilevel detail support.

    Provides comprehensive help for all FastSearch MCP tools with three detail levels:
    basic (quick overview), intermediate (detailed), and advanced (comprehensive with examples).

    Args:
        tool_name: Optional name of a specific tool to get help for
        level: Detail level (basic, intermediate, advanced)

    Returns:
        Dictionary containing tool documentation at the specified detail level
    """
    # Get tools from tools module directly using __all__
    tools_list = []
    try:
        import fastsearch_mcp.tools

        # Use __all__ to get all exported tool functions
        if hasattr(fastsearch_mcp.tools, "__all__"):
            for tool_name_in_list in fastsearch_mcp.tools.__all__:
                # Skip the help tool itself to avoid recursion
                if tool_name_in_list == "help":
                    continue

                if hasattr(fastsearch_mcp.tools, tool_name_in_list):
                    attr = getattr(fastsearch_mcp.tools, tool_name_in_list)
                    # FastMCP wraps tools in FunctionTool objects - get the underlying function
                    func = None
                    if hasattr(attr, "fn"):
                        # FastMCP FunctionTool - get the actual function
                        func = attr.fn
                    elif hasattr(attr, "__wrapped__"):
                        # Standard wrapped function
                        func = attr.__wrapped__
                    elif callable(attr) and not isinstance(attr, type):
                        # Plain function
                        func = attr

                    if func and callable(func):
                        tools_list.append(func)
    except Exception as e:
        logger.error("Error getting tools from module: %s", e, exc_info=True)

    if tool_name:
        return _get_tool_help(tool_name, level, tools_list)
    else:
        return _list_all_tools(level, tools_list)


def _list_all_tools(level: str, tools_list: list) -> dict[str, Any]:
    """List all available tools with appropriate detail level."""
    tools = []

    for tool_func in tools_list:
        try:
            if not hasattr(tool_func, "__name__"):
                continue

            name = tool_func.__name__
            doc = inspect.getdoc(tool_func) or ""

            # Get signature - handle wrapped functions
            try:
                sig = inspect.signature(tool_func)
            except (ValueError, TypeError):
                # If signature fails, try unwrapped version
                if hasattr(tool_func, "__wrapped__"):
                    sig = inspect.signature(tool_func.__wrapped__)
                else:
                    # Skip if we can't get signature
                    continue

            if level == "basic":
                desc = doc.split("\n")[0] if doc else "No description"
                tools.append(f"{name} - {desc[:60]}...")
            elif level == "intermediate":
                params = list(sig.parameters.keys())
                tools.append(
                    {
                        "name": name,
                        "description": doc.split("\n")[0] if doc else "No description",
                        "parameters": len(params),
                    }
                )
            else:  # advanced
                params = []
                for param_name, param in sig.parameters.items():
                    params.append(
                        {
                            "name": param_name,
                            "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                            "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                            "required": param.default == inspect.Parameter.empty,
                        }
                    )
                tools.append(
                    {
                        "name": name,
                        "description": doc,
                        "parameters": params,
                        "return_type": str(sig.return_annotation)
                        if sig.return_annotation != inspect.Signature.empty
                        else "Any",
                    }
                )
        except Exception as e:
            logger.debug("Error processing tool %s: %s", getattr(tool_func, "__name__", "unknown"), e)
            continue

    result = {
        "message": "FastSearch MCP Tools",
        "level": level,
        "count": len(tools),
        "tools": tools,
    }

    return result


def _get_tool_help(tool_name: str, level: str, tools_list: list) -> dict[str, Any]:
    """Get help for a specific tool with multilevel detail."""
    # Find the tool - try exact match first, then case-insensitive
    tool_func = None
    for tf in tools_list:
        if hasattr(tf, "__name__"):
            if tf.__name__ == tool_name:
                tool_func = tf
                break
            # Also try case-insensitive match
            elif tf.__name__.lower() == tool_name.lower():
                tool_func = tf
                break

    if not tool_func:
        available = [tf.__name__ for tf in tools_list if hasattr(tf, "__name__")]
        return {
            "tool": tool_name,
            "level": level,
            "error": "Tool not found",
            "available_tools": available,
            "hint": f"Try one of: {', '.join(available[:10])}" if available else "No tools available",
        }

    doc = inspect.getdoc(tool_func) or "No description"
    sig = inspect.signature(tool_func)

    if level == "basic":
        return {
            "tool": tool_name,
            "level": level,
            "description": doc.split("\n")[0] if doc else "No description",
        }
    elif level == "intermediate":
        params = []
        for param_name, param in sig.parameters.items():
            params.append(
                {
                    "name": param_name,
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                    "description": "",
                    "required": param.default == inspect.Parameter.empty,
                }
            )
        return {
            "tool": tool_name,
            "level": level,
            "description": doc,
            "parameters": params,
            "returns": {
                "type": str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else "Any",
                "description": "",
            },
        }
    else:  # advanced
        params = []
        for param_name, param in sig.parameters.items():
            params.append(
                {
                    "name": param_name,
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                    "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                    "required": param.default == inspect.Parameter.empty,
                }
            )
        return {
            "tool": tool_name,
            "level": level,
            "description": doc,
            "parameters": params,
            "returns": {
                "type": str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else "Any",
                "description": "",
            },
            "examples": _get_examples(tool_name),
        }


def _get_examples(tool_name: str) -> list:
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
                        "search_dir": "D:\\Dev",
                        "file_pattern": "*.py",
                        "max_results": 10,
                    },
                },
            }
        ],
        "analyze_disk_usage": [
            {
                "description": "Analyze C: drive usage",
                "call": {
                    "tool_name": "analyze_disk_usage",
                    "arguments": {"path": "C:\\", "max_depth": 3, "find_large_files": True},
                },
            }
        ],
    }
    return examples.get(tool_name, [])
