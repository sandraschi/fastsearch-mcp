"""Shared MCP instance for tool registration.

FastMCP 3.1: sampling and agentic workflows are supported when clients
connect with a sampling_handler; this server is compatible with the
unified gateway pattern (see fastsearch_mcp.gateway).
"""

from fastmcp import FastMCP

# FastMCP 3.x: identity only; transport (host, port, etc.) passed to run() / http_app()
mcp = FastMCP(name="FastSearch MCP", version="0.4.0")
