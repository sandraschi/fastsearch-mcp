"""Ensure the FastSearch Windows service and named pipe are available."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

from fastsearch_mcp.logging_config import get_logger
from fastsearch_mcp.pipe_client import test_pipe_connection_with_diagnostics
from fastsearch_mcp.service_client import SERVICE_NAME, start_service

logger = get_logger(__name__)

_ENSURE_ENV = "FASTSEARCH_SKIP_ENSURE"
_START_WAIT_SECONDS = 15.0
_POLL_INTERVAL_SECONDS = 0.5


def ensure_enabled() -> bool:
    """Return False when startup ensure is disabled via env."""
    return os.environ.get(_ENSURE_ENV, "").strip().lower() not in {"1", "true", "yes"}


async def _wait_for_pipe(timeout: float = _START_WAIT_SECONDS) -> dict[str, Any]:
    """Poll pipe diagnostics until ping succeeds or timeout."""
    deadline = asyncio.get_event_loop().time() + timeout
    last_diag: dict[str, Any] = {
        "connected": False,
        "ping_ok": False,
        "error_message": "Timed out waiting for pipe",
    }
    while asyncio.get_event_loop().time() < deadline:
        last_diag = await test_pipe_connection_with_diagnostics()
        if last_diag.get("connected") and last_diag.get("ping_ok"):
            return last_diag
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
    return last_diag


async def ensure_service_available(start_if_needed: bool = True) -> dict[str, Any]:
    """Verify pipe connectivity; optionally start the Windows service and retry.

    Safe to call on MCP startup. Does not restart a hung service (use the
    scheduled watchdog script for that).
    """
    if sys.platform != "win32":
        return {
            "success": False,
            "platform": sys.platform,
            "error": "FastSearch service is Windows-only",
        }

    diag = await test_pipe_connection_with_diagnostics()
    if diag.get("connected") and diag.get("ping_ok"):
        return {
            "success": True,
            "action": "none",
            "service_name": SERVICE_NAME,
            "pipe_name": diag.get("pipe_name"),
        }

    if not start_if_needed:
        return {
            "success": False,
            "action": "skipped_start",
            "service_name": SERVICE_NAME,
            "pipe_name": diag.get("pipe_name"),
            "error_code": diag.get("error_code"),
            "error_message": diag.get("error_message") or "Pipe unavailable",
        }

    logger.warning(
        "FastSearch pipe unavailable (connected=%s, error=%s); attempting service start",
        diag.get("connected"),
        diag.get("error_message") or diag.get("error_code"),
    )

    started = await start_service()
    if not started:
        return {
            "success": False,
            "action": "start_failed",
            "service_name": SERVICE_NAME,
            "pipe_name": diag.get("pipe_name"),
            "error": "Could not start FastSearch service (admin may be required)",
            "error_code": diag.get("error_code"),
            "error_message": diag.get("error_message"),
        }

    diag = await _wait_for_pipe()
    if diag.get("connected") and diag.get("ping_ok"):
        logger.info("FastSearch service is available after start")
        return {
            "success": True,
            "action": "started",
            "service_name": SERVICE_NAME,
            "pipe_name": diag.get("pipe_name"),
        }

    return {
        "success": False,
        "action": "start_timeout",
        "service_name": SERVICE_NAME,
        "pipe_name": diag.get("pipe_name"),
        "error": "Service started but pipe ping still failing",
        "error_code": diag.get("error_code"),
        "error_message": diag.get("error_message"),
    }
