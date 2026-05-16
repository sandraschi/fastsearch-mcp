"""
Low-level named pipe client for the FastSearch C++ Windows service.

Usage:
    from fastsearch_pipe_client import FastSearchClient

    # Async
    async with FastSearchClient() as client:
        results = await client.search("*.txt", "C:\\")

    # Sync (runs own event loop)
    client = FastSearchClient()
    results = client.search_sync("*.txt", "C:\\")
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import struct
import sys
from typing import Any

if sys.platform == "win32":
    try:
        import pywintypes
        import win32file
        import win32pipe

        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        logging.getLogger(__name__).warning(
            "pywin32 not installed. `pip install pywin32` for Windows pipe support."
        )
else:
    WINDOWS_AVAILABLE = False

logger = logging.getLogger(__name__)

DEFAULT_PIPE_NAME = r"\\.\pipe\FastSearchMCP"
MAX_PIPE_BUFFER = 65536


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_pipe_name() -> str:
    """Return the named pipe path.

    Override with the ``FASTSEARCH_PIPE_NAME`` environment variable.
    """
    return (os.environ.get("FASTSEARCH_PIPE_NAME") or DEFAULT_PIPE_NAME).strip()


# ---------------------------------------------------------------------------
# Low-level async pipe client
# ---------------------------------------------------------------------------

class _PipeTransport:
    """Async context manager wrapping the ``win32pipe`` named pipe."""

    def __init__(self, pipe_name: str | None = None):
        self.pipe_name = pipe_name or get_pipe_name()
        self._handle: Any = None
        self._connected = False

    async def __aenter__(self) -> "_PipeTransport":
        await self._connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._disconnect()

    # -- connect / disconnect ------------------------------------------------

    async def _connect(self, timeout: float = 5.0) -> None:
        if not WINDOWS_AVAILABLE:
            raise RuntimeError("fastsearch-pipe-client requires Windows + pywin32")
        loop = asyncio.get_event_loop()
        self._handle = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: win32file.CreateFile(
                    self.pipe_name,
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None,
                ),
            ),
            timeout=timeout,
        )
        await loop.run_in_executor(
            None,
            lambda: win32pipe.SetNamedPipeHandleState(
                self._handle, win32pipe.PIPE_READMODE_MESSAGE, None, None
            ),
        )
        self._connected = True

    async def _disconnect(self) -> None:
        if self._handle and self._connected:
            try:
                win32file.CloseHandle(self._handle)
            except Exception:
                pass
        self._handle = None
        self._connected = False

    # -- request / response --------------------------------------------------

    async def request(self, payload: dict, timeout: float = 120.0) -> dict:
        """Send a JSON-RPC-like request and return the parsed response."""
        if not self._connected or not self._handle:
            raise RuntimeError("Not connected to named pipe")

        def _sync_io() -> dict | None:
            data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
            win32file.WriteFile(self._handle, struct.pack("<I", len(data)))
            win32file.WriteFile(self._handle, data)
            win32file.FlushFileBuffers(self._handle)

            raw_len = win32file.ReadFile(self._handle, 4)[1]
            resp_len = struct.unpack("<I", raw_len)[0]
            if resp_len > MAX_PIPE_BUFFER:
                raise RuntimeError(f"Response too large: {resp_len} bytes")
            raw = win32file.ReadFile(self._handle, resp_len)[1]
            return json.loads(raw.decode("utf-8"))

        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, _sync_io), timeout=timeout
            )
        except asyncio.TimeoutError:
            await self._disconnect()
            raise RuntimeError(f"Request timed out after {timeout}s") from None


# ---------------------------------------------------------------------------
# High-level client
# ---------------------------------------------------------------------------

class FastSearchClient:
    """Async client for the FastSearch Windows service.

    Typical usage::

        async with FastSearchClient() as client:
            results = await client.search("*.py", "C:\\Projects")
            info = await client.service_info()
    """

    def __init__(self, pipe_name: str | None = None):
        self._pipe_name = pipe_name or get_pipe_name()
        self._transport: _PipeTransport | None = None

    async def __aenter__(self) -> "FastSearchClient":
        self._transport = _PipeTransport(self._pipe_name)
        await self._transport.__aenter__()
        return self

    async def __aexit__(self, *a: Any) -> None:
        if self._transport:
            await self._transport.__aexit__(*a)

    # -- public methods ------------------------------------------------------

    async def search(
        self,
        pattern: str,
        directory: str = ".",
        max_results: int = 100,
        timeout: float = 120.0,
    ) -> list[dict]:
        """Search for files by name glob via direct NTFS MFT access.

        Returns a list of result dicts with keys: ``path``, ``name``,
        ``size``, ``created``, ``modified``, ``accessed``, ``is_directory``,
        etc.
        """
        if not self._transport:
            raise RuntimeError("Use 'async with FastSearchClient()' or connect() first")
        resp = await self._transport.request(
            {"command": "search_files", "pattern": pattern, "directory": directory, "max_results": max_results},
            timeout=timeout,
        )
        if resp.get("success"):
            return resp.get("results", [])
        raise RuntimeError(resp.get("error", "Search failed"))

    async def ping(self, timeout: float = 3.0) -> bool:
        """Check whether the service is responsive."""
        if not self._transport:
            return False
        try:
            resp = await self._transport.request({"command": "ping"}, timeout=timeout)
            return bool(resp and resp.get("success"))
        except Exception:
            return False

    async def service_info(self, timeout: float = 5.0) -> dict | None:
        """Return metadata from the service (version, timestamp, etc.)."""
        if not self._transport:
            return None
        try:
            resp = await self._transport.request({"command": "get_service_info"}, timeout=timeout)
            if resp and resp.get("success"):
                return resp.get("info")
        except Exception:
            pass
        return None

    # -- sync convenience ----------------------------------------------------

    def search_sync(self, pattern: str, directory: str = ".", max_results: int = 100) -> list[dict]:
        """Synchronous version of :meth:`search` (runs a temporary event loop)."""
        async def _run() -> list[dict]:
            async with FastSearchClient(self._pipe_name) as c:
                return await c.search(pattern, directory, max_results)
        return asyncio.run(_run())

    def ping_sync(self) -> bool:
        """Synchronous version of :meth:`ping`."""
        async def _run() -> bool:
            async with FastSearchClient(self._pipe_name) as c:
                return await c.ping()
        return asyncio.run(_run())


# ---------------------------------------------------------------------------
# Module-level convenience functions  (sync, no class needed)
# ---------------------------------------------------------------------------

def search_files(pattern: str, directory: str = ".", max_results: int = 100) -> list[dict]:
    """Quick one-shot file search.

    Equivalent to ``FastSearchClient().search_sync(...)``.
    """
    return FastSearchClient().search_sync(pattern, directory, max_results)


def get_service_info() -> dict | None:
    """Quick one-shot service info."""
    try:
        return FastSearchClient().ping_sync()  # use ping to test, fallback
    except Exception:
        return None


def test_connection() -> bool:
    """Return ``True`` if the named pipe is reachable and responds to ping."""
    try:
        return FastSearchClient().ping_sync()
    except Exception:
        return False
