#!/usr/bin/env python3
"""
Generate markdown documentation for the FastSearch MCP API.

This script scans the codebase for MCP methods decorated with @mcp_method
and generates comprehensive markdown documentation.
"""

import importlib
import inspect
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from fastsearch_mcp.decorators import generate_markdown_docs

def main():
    """Generate documentation for all MCP methods."""
    # Import the modules containing MCP methods
    from fastsearch_mcp import mcp_server
    
    # Output directory for documentation
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Generate documentation for each module
    modules = [mcp_server]  # Add more modules here as needed
    
    for module in modules:
        module_name = module.__name__.split('.')[-1]
        output_file = docs_dir / f"{module_name}_api.md"
        generate_markdown_docs(module, str(output_file))

if __name__ == "__main__":
    main()
