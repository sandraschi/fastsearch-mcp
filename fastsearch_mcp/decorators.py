"""
Decorators for MCP method documentation and validation.

These decorators serve a dual purpose:
1. Provide rich, structured documentation for MCP methods
2. Generate markdown documentation automatically
"""

import inspect
import json
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from pydantic import BaseModel, create_model

# Type variable for generic function typing
F = TypeVar('F', bound=Callable[..., Any])

@dataclass
class MCPMethodDoc:
    """Documentation model for MCP methods."""
    name: str
    description: str
    params: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    returns: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    source_file: str = ""
    source_line: int = 0
    
    def to_markdown(self) -> str:
        """Convert documentation to markdown format."""
        lines = [
            f"## `{self.name}`",
            "",
            self.description,
            "",
            "### Parameters",
            ""
        ]
        
        # Add parameters
        if not self.params:
            lines.append("*No parameters*")
        else:
            lines.append("| Name | Type | Required | Default | Description |")
            lines.append("|------|------|----------|---------|-------------|")
            for name, param in self.params.items():
                param_type = param.get('type', 'any')
                if 'enum' in param:
                    param_type = f"{'&#124;'.join(param['enum'])}"
                required = "**Yes**" if param.get('required', False) else "No"
                default = f"`{param['default']}`" if 'default' in param else ""
                lines.append(
                    f"| `{name}` | {param_type} | {required} | {default} | "
                    f"{param.get('description', '')} |"
                )
        
        # Add return value
        lines.extend([
            "",
            "### Returns",
            "",
            f"```json\n{json.dumps(self.returns, indent=2)}\n```",
            ""
        ])
        
        # Add examples
        if self.examples:
            lines.extend(["### Examples", ""])
            for i, example in enumerate(self.examples, 1):
                lines.extend([
                    f"#### Example {i}",
                    "",
                    "**Request:**",
                    "```json",
                    json.dumps({"method": self.name, "params": example["request"]}, indent=2),
                    "```",
                    "",
                    "**Response:**",
                    "```json",
                    json.dumps({"result": example["response"]}, indent=2),
                    "```",
                    ""
                ])
        
        # Add source location
        if self.source_file and self.source_line:
            lines.extend([
                "---",
                f"*Defined in `{self.source_file}`, line {self.source_line}*"
            ])
        
        return "\n".join(lines)

def mcp_method(
    name: str,
    description: str,
    params: Optional[Dict[str, Dict[str, Any]]] = None,
    returns: Optional[Dict[str, Any]] = None,
    examples: Optional[List[Dict[str, Any]]] = None
):
    """
    Decorator for documenting MCP methods.
    
    Args:
        name: Full method name (e.g., 'fastsearch.search')
        description: Detailed description of the method
        params: Parameter specifications
        returns: Return value specification
        examples: List of example request/response pairs
    """
    def decorator(func: F) -> F:
        # Get source file and line for documentation
        frame = inspect.currentframe()
        try:
            # Go up two frames to get to the actual function definition
            if frame and frame.f_back and frame.f_back.f_back:
                frame_info = inspect.getframeinfo(frame.f_back.f_back)
                source_file = frame_info.filename
                source_line = frame_info.lineno
            else:
                source_file = ""
                source_line = 0
        finally:
            del frame  # Avoid reference cycles
        
        # Create documentation object
        doc = MCPMethodDoc(
            name=name,
            description=description,
            params=params or {},
            returns=returns or {},
            examples=examples or [],
            source_file=source_file,
            source_line=source_line
        )
        
        # Store documentation in the function
        if not hasattr(func, "__mcp_docs__"):
            func.__mcp_docs__ = []
        func.__mcp_docs__.append(doc)
        
        # Add documentation to the function's docstring
        func.__doc__ = doc.to_markdown()
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
            
        # Copy the documentation to the wrapper
        wrapper.__mcp_docs__ = getattr(func, "__mcp_docs__", [])
        wrapper.__doc__ = func.__doc__
        
        return cast(F, wrapper)
    
    return decorator

def generate_markdown_docs(module, output_file: str) -> None:
    """
    Generate markdown documentation for all MCP methods in a module.
    
    Args:
        module: The module to document
        output_file: Path to the output markdown file
    """
    docs = []
    
    # Find all functions with MCP documentation
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and hasattr(obj, "__mcp_docs__"):
            for doc in obj.__mcp_docs__:
                docs.append((doc.name, doc))
    
    # Sort by method name
    docs.sort(key=lambda x: x[0])
    
    # Generate markdown
    lines = [
        "# FastSearch MCP API Documentation",
        "",
        "## Table of Contents",
        ""
    ]
    
    # Add table of contents
    for name, doc in docs:
        lines.append(f"- [`{name}`](#{name.replace('.', '').lower()})")
    
    # Add method documentation
    for name, doc in docs:
        lines.extend(["", "", doc.to_markdown()])
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"Documentation generated: {output_file}")
