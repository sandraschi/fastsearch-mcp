"""Shared MCP instance for tool registration.

FastMCP 3.2: sampling via ctx.sampling(), CodeMode via --agentic flag,
@mcp.prompt(), and @mcp.skill() decorators. Compatible with unified
gateway pattern (see fastsearch_mcp.gateway).
"""

from fastmcp import FastMCP

mcp = FastMCP(name="FastSearch MCP", version="0.5.0")
