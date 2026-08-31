"""FastMCP 2.13 compliant MCP server.

This module implements the MCP server that communicates with the FastSearch Windows service
via named pipes for performing high-performance NTFS searches.
"""

import asyncio
import ctypes
import json
import logging
import sys
import time
import uuid
from typing import Any

from fastmcp import FastMCP

from .pipe_client import NamedPipeClient
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class McpServer:
    """FastMCP 2.13 compliant MCP server."""

    def __init__(self, pipe_name: str = r"\\.\pipe\fastsearch-service"):
        """Initialize the MCP server.

        Args:
            pipe_name: Name of the named pipe to connect to.
        """
        self.pipe_name = pipe_name
        self.pipe_client = NamedPipeClient(pipe_name)
        self.app = FastMCP("fastsearch-mcp")
        self._running = False
        self._shutdown_event = asyncio.Event()
        self.service_available = False  # Track if the service is available

        # Session management
        self.session_manager = SessionManager()

        # Session management
        self.sessions = {}  # session_id -> session_data
        self.session_timeout = 3600  # 1 hour session timeout
        self._session_cleanup_task = None

        # Register FastMCP 2.13 tools
        self._register_tools()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.pipe_client.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    def _show_service_error_dialog(self, error_message: str):
        """Show a Windows message box with service error and instructions.

        Args:
            error_message: The error message to display
        """
        if sys.platform == "win32":
            try:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"{error_message}\n\n"
                    "To start the FastSearch service:\n"
                    "1. Open Windows Services (press Win+R, type 'services.msc', press Enter)\n"
                    "2. Locate 'FastSearch Service' in the list\n"
                    "3. Right-click and select 'Start'\n\n"
                    "If the service is not installed, please run the installer as administrator.",
                    "FastSearch Service Not Running",
                    0x40 | 0x1,  # MB_ICONINFORMATION | MB_OK
                )
            except Exception as e:
                logger.warning(f"Failed to show error dialog: {e}")

    async def _cleanup_sessions(self):
        """Background task to clean up expired sessions."""
        while self._running:
            try:
                now = time.time()
                expired = [
                    sid
                    for sid, session in self.sessions.items()
                    if now - session.get("last_activity", 0) > self.session_timeout
                ]

                for sid in expired:
                    logger.debug(f"Cleaning up expired session: {sid}")
                    del self.sessions[sid]

            except Exception as e:
                logger.error(f"Error cleaning up sessions: {e}", exc_info=True)

            await asyncio.sleep(300)  # Check every 5 minutes

    async def start(self, stdin=None, stdout=None):
        """Start the MCP server.

        Args:
            stdin: Input stream (default: sys.stdin)
            stdout: Output stream (default: sys.stdout)

        Raises:
            RuntimeError: If the FastSearch service is not available
        """

        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout

        self._running = True
        self._shutdown_event.clear()

        # Start session manager
        await self.session_manager.start()

        # Start session cleanup task
        self._session_cleanup_task = asyncio.create_task(self._cleanup_sessions())

        # Try to connect to the pipe, but don't fail if we can't
        try:
            self.service_available = await self.pipe_client.connect()
            if self.service_available:
                logger.info("Successfully connected to FastSearch service")
            else:
                logger.warning("Running in offline mode - some functionality may be limited")

        except Exception as e:
            self.service_available = False
            logger.warning(f"Running in offline mode - could not connect to service: {e}")
            self._show_service_error_dialog(
                f"Running in limited mode. Some features require the FastSearch service.\n\nError: {e!s}"
            )

        try:
            # Main message loop
            while self._running and not self._shutdown_event.is_set():
                try:
                    # Read a line from stdin with timeout
                    try:
                        line = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(None, stdin.readline),
                            timeout=1.0,  # Check for shutdown every second
                        )

                        if not line:
                            logger.debug("Received EOF on stdin, but continuing to run")
                            await asyncio.sleep(1)  # Small delay to prevent busy waiting
                            continue

                        # Process the message
                        response = await self._process_message(line.strip())
                        if response:
                            # Write response to stdout
                            await asyncio.get_event_loop().run_in_executor(
                                None, lambda r=response: stdout.write(f"{r}\n") or stdout.flush()
                            )

                    except TimeoutError:
                        # Timeout is expected, just continue the loop
                        continue

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Continue running even if there's an error with one message
                    await asyncio.sleep(1)  # Prevent tight error loops

        except asyncio.CancelledError:
            logger.info("Server task was cancelled")
        except Exception:
            logger.exception("Fatal error in MCP server")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """Stop the MCP server."""
        self._running = False
        self._shutdown_event.set()
        await self.session_manager.stop()
        if self._session_cleanup_task:
            self._session_cleanup_task.cancel()
            try:
                await self._session_cleanup_task
            except asyncio.CancelledError:
                pass
        await self.pipe_client.close()

    def _get_or_create_session(self, session_id: str | None = None) -> str:
        """Get existing session or create a new one.

        Args:
            session_id: Optional session ID to look up

        Returns:
            Session ID and session data
        """
        now = time.time()

        if session_id and session_id in self.sessions:
            # Update last activity for existing session
            self.sessions[session_id]["last_activity"] = now
            return session_id, self.sessions[session_id]

        # Create new session
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {"created_at": now, "last_activity": now, "data": {}}
        return session_id, self.sessions[session_id]

    async def _process_message(self, message: str) -> str | None:
        """Process a single incoming message.

        Args:
            message: The incoming message string

        Returns:
            Response string or None if no response needed
        """
        try:
            # Parse the JSON-RPC message
            request = json.loads(message)
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id")

            # Handle session
            session_id = params.pop("session_id", None)
            session_id, session = self.session_manager.get_or_create_session(session_id)
            params["_session"] = session["data"]
            params["_session_id"] = session_id

            # Route to the appropriate handler
            if hasattr(self, method):
                result = await getattr(self, method)(**params)

                # Format response with session ID
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result,
                    "session_id": session_id,
                }

                # Don't include session data in the response
                if isinstance(result, dict) and "_session" in result:
                    del response["result"]["_session"]

                return json.dumps(response, ensure_ascii=True)

            else:
                return json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Method not found: {method}"},
                    },
                    ensure_ascii=True,
                )

        except json.JSONDecodeError as e:
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error", "data": str(e)},
                },
                ensure_ascii=True,
            )

        except Exception as e:
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": request_id if "request_id" in locals() else None,
                    "error": {"code": -32603, "message": "Internal error", "data": str(e)},
                },
                ensure_ascii=True,
            )

    def _register_tools(self):
        """Register all tools with FastMCP 2.13."""
        # Register fastsearch.search
        self.app.tool(name="fastsearch.search")(self.handle_search)

        # Register getStatus
        self.app.tool(name="getStatus")(self.get_status)

        # Note: No fallback search tool - direct MFT access via service is REQUIRED
        # Treewalking fallbacks violate the architecture (direct NTFS MFT access only)

    async def handle_search(
        self,
        query: str,
        search_type: str = "glob",
        limit: int = 100,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        case_sensitive: bool = False,
        path: str = "C:\\",
        _session: dict | None = None,
    ) -> dict[str, Any]:
        """Search for files using the FastSearch service.

        Args:
            query: The search query (pattern, regex, or exact text)
            search_type: Type of search (glob, regex, exact, fuzzy)
            limit: Maximum number of results to return
            include: List of file patterns to include
            exclude: List of file patterns to exclude
            case_sensitive: Whether the search is case-sensitive
            path: Root path to search within
            _session: Injected session data

        Returns:
            Dict containing search results and statistics

        Raises:
            RuntimeError: If the service is not available or search fails
        """
        if not self.service_available:
            raise RuntimeError(
                "FastSearch service is not available. Please ensure the service is installed and running."
            )

        # Prepare search parameters
        search_id = str(uuid.uuid4())
        search_timestamp = time.time()

        try:
            # Call the underlying search implementation
            results = await self._perform_search(
                query=query,
                search_type=search_type,
                limit=limit,
                include=include or [],
                exclude=exclude or [],
                case_sensitive=case_sensitive,
                path=path,
            )

            # Store search in session history if session exists
            if _session is not None:
                search_entry = {
                    "id": search_id,
                    "timestamp": search_timestamp,
                    "query": query,
                    "search_type": search_type,
                    "path": path,
                    "result_count": len(results.get("results", [])),
                    "duration_ms": (time.time() - search_timestamp) * 1000,
                }

                if "search_history" not in _session:
                    _session["search_history"] = []

                # Keep only the 100 most recent searches
                _session["search_history"] = ([search_entry] + _session["search_history"])[:100]

            return {
                "results": results.get("results", []),
                "stats": {
                    "total_found": len(results.get("results", [])),
                    "search_time_ms": (time.time() - search_timestamp) * 1000,
                },
                "search_id": search_id,
            }

        except Exception as e:
            raise RuntimeError(f"Search failed: {e}") from e

    async def get_status(self) -> dict[str, Any]:
        """Get the current status of the FastSearch service.

        Returns a detailed status including:
        - Whether the service is installed
        - Current service state (running/stopped/disabled)
        - Service executable path if available
        - Connection status to the service
        """
        try:
            import os

            import win32api
            import win32con
            import win32service
            import win32serviceutil

            service_name = "FastSearch"
            status = {
                "service_available": False,
                "status": "Unknown",
                "details": {},
                "suggestions": [],
            }

            # Check if service is installed and get its status
            try:
                service_status = win32serviceutil.QueryServiceStatus(service_name)
                state = service_status[1]
            except Exception as service_error:
                # Service query failed
                if "service does not exist" in str(service_error).lower():
                    return {
                        "service_available": False,
                        "status": "Service not installed",
                        "details": {"error": "The FastSearch service is not installed on this system"},
                        "suggestions": [
                            "Install the FastSearch service using the installer",
                            "Check if the installation completed successfully",
                        ],
                    }
                raise

            # Map Windows service states to human-readable strings
            state_map = {
                win32service.SERVICE_STOPPED: "Stopped",
                win32service.SERVICE_START_PENDING: "Starting",
                win32service.SERVICE_STOP_PENDING: "Stopping",
                win32service.SERVICE_RUNNING: "Running",
                win32service.SERVICE_CONTINUE_PENDING: "Resuming",
                win32service.SERVICE_PAUSE_PENDING: "Pausing",
                win32service.SERVICE_PAUSED: "Paused",
            }

            state_str = state_map.get(state, f"Unknown state ({state})")

            # Get service binary path from registry
            try:
                key = win32api.RegOpenKey(
                    win32con.HKEY_LOCAL_MACHINE,
                    f"SYSTEM\\CurrentControlSet\\Services\\{service_name}",
                    0,
                    win32con.KEY_READ,
                )

                try:
                    image_path = win32api.RegQueryValueEx(key, "ImagePath")[0]
                    # Clean up the path (remove quotes and expand environment variables)
                    image_path = image_path.strip('"')
                    image_path = os.path.expandvars(image_path)
                except OSError:
                    image_path = "Not found"

                win32api.RegCloseKey(key)

            except Exception as e:
                image_path = f"Error retrieving path: {e!s}"

            # Check if we can connect to the service
            can_connect = False
            try:
                test_client = NamedPipeClient(self.pipe_name, timeout=1.0)
                await test_client.connect()
                can_connect = True
                await test_client.close()
            except Exception:
                pass

            # Build the status response
            status.update(
                {
                    "service_available": state == win32service.SERVICE_RUNNING and can_connect,
                    "status": state_str,
                    "details": {
                        "service_state": state_str,
                        "service_name": service_name,
                        "executable_path": image_path,
                        "pipe_connection_available": can_connect,
                        "pipe_name": self.pipe_name,
                        "service_running": state == win32service.SERVICE_RUNNING,
                    },
                    "suggestions": [
                        "Start the service using: 'net start FastSearch' (as administrator)"
                        if state != win32service.SERVICE_RUNNING
                        else "",
                        "Check service logs for errors"
                        if not can_connect and state == win32service.SERVICE_RUNNING
                        else "",
                    ],
                }
            )

            # Remove empty suggestions
            status["suggestions"] = [s for s in status["suggestions"] if s]

            return status

        except Exception as e:
            # Other error checking service status
            return {
                "service_available": False,
                "status": f"Error checking service status: {e!s}",
                "details": {"error": str(e)},
                "suggestions": [
                    "Check if you have administrator privileges",
                    "Verify the service is properly installed",
                ],
            }

        except ImportError:
            # Fallback for non-Windows or missing pywin32
            return {
                "service_available": False,
                "status": "Windows service API not available",
                "details": {"error": "This feature requires Windows and pywin32 package"},
                "suggestions": [
                    "Install pywin32: pip install pywin32",
                    "This feature is only available on Windows",
                ],
            }

    async def get_capabilities(self) -> dict[str, Any]:
        """Return capabilities of the FastSearch service."""
        capabilities = {
            "fastsearch": {
                "version": "1.0.0",
                "capabilities": ["search", "status"],
                "search_types": ["glob", "regex", "exact", "fuzzy"],
                "service_available": getattr(self, "service_available", False),
            }
        }

        # Try to get enhanced capabilities if service is available
        if getattr(self, "service_available", False):
            try:
                service_caps = await self.pipe_client.send_request("get_capabilities")
                if service_caps:
                    capabilities["fastsearch"].update(service_caps)
            except Exception as e:
                logger.warning(f"Could not get service capabilities: {e}")

        return capabilities
