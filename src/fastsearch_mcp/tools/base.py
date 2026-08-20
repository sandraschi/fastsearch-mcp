"""Base classes for MCP tools."""

from __future__ import annotations

import abc
import base64
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from types import NoneType
from typing import Any, TypeVar

from fastsearch_mcp.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound="BaseTool")


class ToolCategory(StrEnum):
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
    type: type
    description: str = ""
    required: bool = True
    default: Any = None
    choices: list[Any] | None = None
    min: int | float | None = None
    max: int | float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        result = asdict(self)
        # Convert type to string representation
        result["type"] = self.type.__name__
        return result


@dataclass
class ToolDefinition:
    """Complete definition of a tool for registration and documentation."""

    name: str
    description: str
    category: ToolCategory
    parameters: list[ToolParameter] = field(default_factory=list)
    return_type: type = field(default_factory=lambda: type(None))
    return_description: str = ""
    requires_elevation: bool = False
    tags: set[str] | None = None
    enabled: bool = True
    exclude_args: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": [p.to_dict() for p in self.parameters],
            "return_type": self.return_type.__name__,
            "return_description": self.return_description,
            "requires_elevation": self.requires_elevation,
            "tags": list(self.tags) if self.tags else [],
            "enabled": self.enabled,
            "exclude_args": self.exclude_args or [],
        }


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively sanitize data structure to ensure all strings are ASCII-safe."""
    if isinstance(obj, str):
        # Replace non-ASCII characters with ASCII equivalents or remove them
        return obj.encode("ascii", errors="replace").decode("ascii")
    elif isinstance(obj, dict):
        return {_sanitize_for_json(k): _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_sanitize_for_json(item) for item in obj)
    elif isinstance(obj, bytes):
        return base64.b64encode(obj).decode("ascii")
    else:
        return obj


class BaseTool(abc.ABC):
    """Base class for all MCP tools."""

    def __init_subclass__(cls, **kwargs):
        """Register the tool when a subclass is created."""
        super().__init_subclass__(**kwargs)
        # Tool registration is now handled by the @tool decorator

    # get_definition method will be added by the @tool decorator

    @abc.abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with the given parameters."""
        raise NotImplementedError


class ToolRegistry:
    """Registry for all available tools."""

    _instance = None
    _tools: dict[str, BaseTool] = {}

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
    def get_tool(cls, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> dict[str, dict[str, Any]]:
        """List all registered tools with their definitions."""
        return {name: tool.get_definition().to_dict() for name, tool in cls._tools.items()}

    @classmethod
    def get_tool_schema(cls, name: str) -> dict[str, Any] | None:
        """Get the JSON schema for a tool's parameters."""
        tool = cls.get_tool(name)
        if not tool:
            return None

        definition = tool.get_definition()
        schema = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

        for param in definition.parameters:
            param_schema = {"type": param.type.__name__.lower()}
            if param.choices:
                param_schema["enum"] = param.choices
            if param.min is not None:
                param_schema["minimum"] = param.min
            if param.max is not None:
                param_schema["maximum"] = param.max
            if not param.required:
                param_schema["default"] = param.default

            schema["properties"][param.name] = param_schema
            if param.required:
                schema["required"].append(param.name)

        return schema


def tool(
    name: str,
    description: str,
    category: ToolCategory,
    parameters: list[ToolParameter] | None = None,
    return_type: type = NoneType,
    return_description: str = "",
    requires_elevation: bool = False,
    tags: set[str] | None = None,
    enabled: bool = True,
    exclude_args: list[str] | None = None,
) -> Callable[[type[T]], type[T]]:
    """Decorator to register a tool with its definition.

    Args:
        name: Unique name of the tool
        description: Description of what the tool does
        category: Category for organizing the tool
        parameters: List of tool parameters
        return_type: Type of the return value
        return_description: Description of the return value
        requires_elevation: Whether the tool requires elevated privileges
        tags: Set of tags for categorizing the tool
        enabled: Whether the tool is enabled
        exclude_args: List of argument names to exclude from tool schema
    """
    if parameters is None:
        parameters = []

    def decorator(cls: type[T]) -> type[T]:
        # Create the tool definition
        definition = ToolDefinition(
            name=name,
            description=description,
            category=category,
            parameters=parameters,
            return_type=return_type,
            return_description=return_description,
            requires_elevation=requires_elevation,
            tags=tags,
            enabled=enabled,
            exclude_args=exclude_args,
        )

        # Add the get_definition method to the class
        def get_definition(cls) -> ToolDefinition:
            return definition

        cls.get_definition = classmethod(get_definition)

        # Register the tool in the registry
        ToolRegistry.register_tool(cls())

        return cls

    return decorator
