"""
FastSearch MCP Tools

This package contains tools that can be registered with the MCP server.
Each tool is a Python function that can be called remotely via the MCP protocol.
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from functools import wraps
import inspect
import json

ToolHandler = Callable[..., Awaitable[Any]]

@dataclass
class ToolInfo:
    """Metadata about a registered tool."""
    name: str
    handler: ToolHandler
    description: str
    parameters: dict
    returns: dict

def tool(name: str, description: str = ""):
    """
    Decorator to register a function as an MCP tool.
    
    Args:
        name: The name of the tool (e.g., 'fastsearch.search')
        description: A short description of what the tool does
    """
    def decorator(func):
        # Extract parameter information
        sig = inspect.signature(func)
        parameters = {}
        
        for param in sig.parameters.values():
            param_info = {
                'type': param.annotation.__name__ if param.annotation != inspect.Parameter.empty else 'Any',
                'default': str(param.default) if param.default != inspect.Parameter.empty else None,
                'required': param.default == inspect.Parameter.empty,
            }
            if param.annotation != inspect.Parameter.empty:
                param_info['type'] = param.annotation.__name__
            parameters[param.name] = param_info
        
        # Get return type info
        return_type = 'Any'
        if sig.return_annotation != inspect.Signature.empty:
            return_type = sig.return_annotation.__name__
        
        # Store metadata
        func._mcp_tool = {
            'name': name,
            'description': description or func.__doc__ or "",
            'parameters': parameters,
            'returns': {'type': return_type}
        }
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator

class ToolRegistry:
    """Registry for MCP tools."""
    
    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}
    
    def register(self, func: ToolHandler) -> None:
        """Register a tool function."""
        if not hasattr(func, '_mcp_tool'):
            raise ValueError("Function must be decorated with @tool")
            
        meta = func._mcp_tool
        self._tools[meta['name']] = ToolInfo(
            name=meta['name'],
            handler=func,
            description=meta['description'],
            parameters=meta['parameters'],
            returns=meta['returns']
        )
    
    def get_tool(self, name: str) -> Optional[ToolInfo]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[dict]:
        """List all registered tools with their metadata."""
        return [
            {
                'name': tool.name,
                'description': tool.description,
                'parameters': tool.parameters,
                'returns': tool.returns
            }
            for tool in self._tools.values()
        ]
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool with the given arguments."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        return await tool.handler(**kwargs)
