"""
Help system for FastSearch MCP Tools.

Provides documentation and usage information for all registered tools.
"""
from typing import Dict, List, Any
from ..mcp_server import McpServer
from . import ToolRegistry

@tool("mcp.help", "List all available tools or get help for a specific tool")
async def help(tool_name: str = None) -> Dict[str, Any]:
    """
    Get help for tools.
    
    Args:
        tool_name: Optional name of a specific tool to get help for
        
    Returns:
        Dictionary containing tool documentation
    """
    from .. import get_global_registry
    registry = get_global_registry()
    
    if tool_name:
        return await _get_tool_help(registry, tool_name)
    return await _list_tools(registry)

async def _list_tools(registry: ToolRegistry) -> Dict[str, Any]:
    """List all available tools."""
    tools = registry.list_tools()
    
    # Categorize tools by namespace
    categories: Dict[str, List[Dict[str, Any]]] = {}
    
    for tool in tools:
        namespace = tool['name'].split('.')[0]
        if namespace not in categories:
            categories[namespace] = []
        categories[namespace].append({
            'name': tool['name'],
            'description': tool['description'].split('\n')[0] if tool['description'] else ""
        })
    
    return {
        'categories': [
            {
                'name': category,
                'tools': tools
            }
            for category, tools in categories.items()
        ],
        'count': len(tools),
        'help': "Use 'mcp.help {tool_name}' for detailed help on a specific tool"
    }

async def _get_tool_help(registry: ToolRegistry, tool_name: str) -> Dict[str, Any]:
    """Get detailed help for a specific tool."""
    tool_info = registry.get_tool(tool_name)
    if not tool_info:
        return {
            'error': f"Tool not found: {tool_name}",
            'available_tools': [t['name'] for t in registry.list_tools()]
        }
    
    # Format parameters
    params = []
    for name, info in tool_info.parameters.items():
        param = {
            'name': name,
            'type': info.get('type', 'Any'),
            'required': info.get('required', True),
            'description': ""
        }
        if 'default' in info and info['default'] is not None:
            param['default'] = info['default']
        params.append(param)
    
    return {
        'name': tool_info.name,
        'description': tool_info.description,
        'parameters': params,
        'returns': tool_info.returns,
        'example': _generate_example(tool_info)
    }

def _generate_example(tool_info: 'ToolInfo') -> Dict[str, Any]:
    """Generate an example request for the tool."""
    example = {
        'method': tool_info.name,
        'params': {}
    }
    
    for name, info in tool_info.parameters.items():
        if 'default' in info and info['default'] is not None:
            example['params'][name] = info['default']
        else:
            # Simple type-based example values
            type_name = info.get('type', '').lower()
            if 'str' in type_name:
                example['params'][name] = f"example_{name}"
            elif 'int' in type_name:
                example['params'][name] = 42
            elif 'bool' in type_name:
                example['params'][name] = True
            elif 'list' in type_name or 'array' in type_name:
                example['params'][name] = []
            elif 'dict' in type_name or 'object' in type_name:
                example['params'][name] = {}
            else:
                example['params'][name] = None
    
    return example
