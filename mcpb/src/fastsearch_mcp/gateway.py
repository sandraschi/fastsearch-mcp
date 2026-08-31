"""
Unified gateway entry point (FastMCP 3.x).

Run FastSearch MCP as a proxy/gateway that aggregates one or more backend MCP servers.
Supports transport bridging (e.g. backend HTTP -> client stdio) and forwards
sampling, elicitation, logging, and progress.

Environment:
  FASTSEARCH_GATEWAY_URL: Single backend URL (e.g. http://127.0.0.1:10845/mcp)
  FASTSEARCH_GATEWAY_CONFIG: JSON path or inline JSON for MCPConfig multi-server
  MCP_TRANSPORT, MCP_HOST, MCP_PORT: How to run this gateway (default: stdio)

Usage:
  uv run python -m fastsearch_mcp.gateway
  FASTSEARCH_GATEWAY_URL=http://other:8000/mcp uv run python -m fastsearch_mcp.gateway
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_gateway_config() -> dict | str:
    url = os.environ.get("FASTSEARCH_GATEWAY_URL", "").strip()
    if url:
        return url
    config_env = os.environ.get("FASTSEARCH_GATEWAY_CONFIG", "").strip()
    if not config_env:
        logger.error("Set FASTSEARCH_GATEWAY_URL or FASTSEARCH_GATEWAY_CONFIG")
        sys.exit(1)
    if config_env.startswith("{"):
        return json.loads(config_env)
    path = Path(config_env)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    logger.error("FASTSEARCH_GATEWAY_CONFIG not a JSON object or file path: %s", config_env)
    sys.exit(1)


def main() -> None:
    try:
        from fastmcp.server import create_proxy
    except ImportError as e:
        logger.error("FastMCP 3.x required for gateway: %s", e)
        sys.exit(1)

    config = _load_gateway_config()
    if isinstance(config, str):
        proxy = create_proxy(config, name="FastSearch Gateway")
    else:
        if "mcpServers" not in config:
            config = {"mcpServers": {"default": config}}
        proxy = create_proxy(config, name="FastSearch Gateway")

    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "stdio":
        logger.info("Running gateway in STDIO mode")
        asyncio.run(proxy.run_stdio_async())
    else:
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8000"))
        path = os.getenv("MCP_PATH", "/mcp")
        logger.info("Running gateway in HTTP mode at http://%s:%s%s", host, port, path)
        asyncio.run(proxy.run_http_async(host=host, port=port, path=path))


if __name__ == "__main__":
    main()
