"""
FastSearch MCP Server - FastMCP 3.x implementation.

FastMCP 3.1: compatible with sampling (client sampling_handler), agentic workflows,
and unified gateway (see fastsearch_mcp.gateway). For web_sota, uvicorn runs this app
(REST bridge at /) so the frontend can list/call tools.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastsearch_mcp.mcp_instance import mcp

logger = logging.getLogger(__name__)

# CRITICAL: Import tools, prompts, and skills to register them with the MCP instance
# This must happen after mcp instance is created but before running server
# Tools are registered via @mcp.tool decorator when imported
# Prompts are registered via @mcp.prompt() decorator when imported
# Skills are registered via @mcp.skill() decorator when imported
import fastsearch_mcp.tools  # noqa: F401
import fastsearch_mcp.prompts  # noqa: F401
import fastsearch_mcp.skills  # noqa: F401

from fastsearch_mcp.api_bridge import router as api_router

# REST app for web_sota: GET /health, GET /tools, POST /tools/:name
app = FastAPI(title="FastSearch MCP")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def root_health() -> dict:
    """Fleet manifest healthPath: /health (no /api prefix)."""
    return {"status": "ok", "service": "fastsearch-mcp"}

# MCP server reference for CLI / stdio
server = mcp
