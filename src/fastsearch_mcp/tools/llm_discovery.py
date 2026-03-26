"""Tool for discovering local LLM models from Ollama and LM Studio."""

import logging
from typing import Any, Dict
import httpx
from fastsearch_mcp.mcp_instance import mcp

logger = logging.getLogger(__name__)


@mcp.tool
async def list_local_models() -> Dict[str, Any]:
    """
    Discover available LLM models from local providers like Ollama and LM Studio.

    Returns:
        A dictionary containing lists of discovered models per provider.
    """
    results = {"ollama": [], "lm_studio": [], "errors": []}

    # 1. Discover Ollama models
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                results["ollama"] = [m["name"] for m in data.get("models", [])]
    except Exception as e:
        logger.debug(f"Ollama discovery failed: {e}")
        results["errors"].append(f"Ollama: {str(e)}")

    # 2. Discover LM Studio models
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("http://localhost:1234/v1/models")
            if response.status_code == 200:
                data = response.json()
                results["lm_studio"] = [m["id"] for m in data.get("data", [])]
    except Exception as e:
        logger.debug(f"LM Studio discovery failed: {e}")
        results["errors"].append(f"LM Studio: {str(e)}")

    return results
