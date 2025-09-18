"""Base classes for MCP tools."""
from __future__ import annotations

import abc
import inspect
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from fastsearch_mcp.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound='BaseTool')


class ToolCategory(str, Enum):
    """Categories for organizing tools in the MCP server."""
    FILESYSTEM = "File System"
    SYSTEM = "System"
    NETWORK = "Network"
    SECURITY = "Security"
    DEVELOPMENT = "Development"
    UTILITIES = "Utilities"


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: Type
    description: str = ""
    required: bool = True
    default: Any = None
    choices: Optional[List[Any]] = None
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        result = asdict(self)
        # Convert type to string representation
        result['type'] = self.type.__name__
        return result


@dataclass
class ToolDefinition:
    """Complete definition of a tool for registration and documentation."""
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter] = field(default_factory=list)
    return_type: Type = type(None)
    return_description: str = ""
    requires_elevation: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'parameters': [p.to_dict() for p in self.parameters],
            'return_type': self.return_type.__name__,
            'return_description': self.return_description,
            'requires_elevation': self.requires_elevation
        }


class BaseTool(abc.ABC):
    """Base class for all MCP tools."""
    
    def __init_subclass__(cls, **kwargs):
        """Register the tool when a subclass is created."""
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            ToolRegistry.register_tool(cls())
    
    @classmethod
    @abc.abstractmethod
    def get_definition(cls) -> ToolDefinition:
        """Return the tool's definition."""
        raise NotImplementedError
    
    @abc.abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with the given parameters."""
        raise NotImplementedError


class ToolRegistry:
    """Registry for all available tools."""
    _instance = None
    _tools: Dict[str, BaseTool] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_tool(cls, tool: BaseTool) -> None:
        """Register a tool with the registry."""
        definition = tool.get_definition()
        if definition.name in cls._tools:
            logger.warning("Tool %s is already registered. Overwriting.", definition.name)
        cls._tools[definition.name] = tool
        logger.debug("Registered tool: %s", definition.name)
    
    @classmethod
    def get_tool(cls, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> Dict[str, Dict[str, Any]]:
        """List all registered tools with their definitions."""
        return {
            name: tool.get_definition().to_dict()
            for name, tool in cls._tools.items()
        }
    
    @classmethod
    def get_tool_schema(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get the JSON schema for a tool's parameters."""
        tool = cls.get_tool(name)
        if not tool:
            return None
            
        definition = tool.get_definition()
        schema = {
            'type': 'object',
            'properties': {},
            'required': [],
            'additionalProperties': False
        }
        
        for param in definition.parameters:
            param_schema = {'type': param.type.__name__.lower()}
            if param.choices:
                param_schema['enum'] = param.choices
            if param.min is not None:
                param_schema['minimum'] = param.min
            if param.max is not None:
                param_schema['maximum'] = param.max
            if not param.required:
                param_schema['default'] = param.default
                
            schema['properties'][param.name] = param_schema
            if param.required:
                schema['required'].append(param.name)
                
        return schema


def tool(
    name: str,
    description: str,
    category: ToolCategory,
    parameters: Optional[List[ToolParameter]] = None,
    return_type: Type = type(None),
    return_description: str = "",
    requires_elevation: bool = False
) -> Callable[[Type[T]], Type[T]]:
    """Decorator to register a tool with its definition.
    
    Args:
        name: Unique name of the tool
        description: Description of what the tool does
        category: Category for organizing the tool
        parameters: List of tool parameters
        return_type: Type of the return value
        return_description: Description of the return value
        requires_elevation: Whether the tool requires elevated privileges
    """
    if parameters is None:
        parameters = []
    
    def decorator(cls: Type[T]) -> Type[T]:
        # Create the tool definition
        definition = ToolDefinition(
            name=name,
            description=description,
            category=category,
            parameters=parameters,
            return_type=return_type,
            return_description=return_description,
            requires_elevation=requires_elevation
        )
        
        # Add the get_definition method to the class
        @classmethod
        def get_definition(cls) -> ToolDefinition:
            return definition
            
        cls.get_definition = get_definition
        
        # Register the tool when the class is created
        original_init_subclass = cls.__init_subclass__
        
        def __init_subclass__(cls, **kwargs):
            original_init_subclass(**kwargs)
            if not inspect.isabstract(cls):
                ToolRegistry.register_tool(cls())
                
        cls.__init_subclass__ = classmethod(__init_subclass__)
        
        return cls
    
    return decorator
