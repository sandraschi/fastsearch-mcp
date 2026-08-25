"""
Service client for communicating with the FastSearch C++ service.

This module provides functions to communicate with the FastSearch C++ service
via named pipes for NTFS MFT access.
"""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Any

from .logging_config import get_logger
from .pipe_client import (
    get_pipe_name,
    get_service_info_via_pipe,
    search_files_via_pipe,
    test_pipe_connection,
)

logger = get_logger(__name__)

# Cache for service status to avoid slow checks on every search
_service_status_cache: tuple[bool, float] | None = None  # (is_running, timestamp)
_CACHE_TTL = 2.0  # Cache for 2 seconds - fast enough for rapid searches, fresh enough

SERVICE_NAME = "FastSearchMCP"
_BIN_DIR = Path(__file__).parent.parent.parent / "service" / "build" / "bin" / "Release"
SERVICE_EXECUTABLE = (
    _BIN_DIR / "FastSearchEngine.exe"
    if (_BIN_DIR / "FastSearchEngine.exe").exists()
    else _BIN_DIR / "FastSearchServiceNew.exe"
)


def is_service_running() -> bool:
    """Check if the FastSearch C++ service is running (fast, cached check).

    Uses a fast pipe connection attempt first (fails immediately if service is down),
    with caching to avoid repeated checks. Falls back to SCM and process checks if needed.

    Returns:
        bool: True if the service is running, False otherwise
    """
    global _service_status_cache

    # Check cache first (fast path for repeated calls)
    now = time.time()
    if _service_status_cache is not None:
        cached_status, cache_time = _service_status_cache
        if now - cache_time < _CACHE_TTL:
            return cached_status

    # 1. Fast check: Try to connect to pipe
    try:
        import pywintypes
        import win32file

        handle = win32file.CreateFile(
            get_pipe_name(),
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )
        win32file.CloseHandle(handle)
        _service_status_cache = (True, now)
        return True
    except pywintypes.error as e:
        # ERROR_PIPE_BUSY (231) or ERROR_ACCESS_DENIED (5) means pipe exists & service is RUNNING!
        if e.winerror in (231, 5):
            _service_status_cache = (True, now)
            return True
        if e.winerror == 2:  # ERROR_FILE_NOT_FOUND - pipe doesn't exist
            pass
    except Exception as e:
        logger.debug(f"Pipe check exception: {e}")

    # 2. Check SCM service state
    try:
        res = subprocess.run(
            ["sc", "query", SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if "STATE" in res.stdout and "RUNNING" in res.stdout:
            _service_status_cache = (True, now)
            return True
    except Exception as e:
        logger.debug(f"SCM query exception: {e}")

    # 3. Fallback: Check process list (tasklist)
    try:
        result = subprocess.run(
            ["tasklist"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        is_running = "FastSearchEngine.exe" in result.stdout or "FastSearchServiceNew.exe" in result.stdout
        _service_status_cache = (is_running, now)
        return is_running
    except subprocess.TimeoutExpired:
        logger.warning("Service check timed out, assuming service is not running")
        _service_status_cache = (False, now)
        return False
    except Exception as e:
        logger.debug(f"Error checking service status: {e}")
        _service_status_cache = (False, now)
        return False


async def get_service_status() -> dict[str, Any]:
    """Get detailed status of the FastSearch C++ service.

    Returns:
        Dict containing service status information
    """
    try:
        # Check if service executable exists
        if not SERVICE_EXECUTABLE.exists():
            return {
                "running": False,
                "error": "Service executable not found",
                "executable_path": str(SERVICE_EXECUTABLE),
            }

        # Check if service process is running
        running = is_service_running()

        # Try to get service info via named pipe if running
        pipe_info = None
        if running:
            try:
                pipe_info = await get_service_info_via_pipe()
            except Exception as e:
                logger.debug(f"Could not get pipe info: {e}")

        # Try to get service info from Windows Service Manager
        try:
            result = await asyncio.to_thread(
                subprocess.run, ["sc", "query", SERVICE_NAME], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                # Parse service status from sc query output
                status_lines = result.stdout.split("\n")
                state = "UNKNOWN"
                for line in status_lines:
                    if "STATE" in line:
                        state = line.split(":")[-1].strip()
                        break

                return {
                    "running": running,
                    "service_state": state,
                    "executable_path": str(SERVICE_EXECUTABLE),
                    "pipe_name": get_pipe_name(),
                    "pipe_info": pipe_info,
                    "pipe_connected": pipe_info is not None,
                }
            else:
                return {
                    "running": running,
                    "error": "Service not installed",
                    "executable_path": str(SERVICE_EXECUTABLE),
                    "pipe_name": get_pipe_name(),
                    "pipe_info": pipe_info,
                    "pipe_connected": pipe_info is not None,
                }
        except Exception as e:
            logger.debug(f"Error querying service: {e}")
            return {
                "running": running,
                "error": f"Service query failed: {e}",
                "executable_path": str(SERVICE_EXECUTABLE),
                "pipe_name": get_pipe_name(),
                "pipe_info": pipe_info,
                "pipe_connected": pipe_info is not None,
            }

    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return {"running": False, "error": str(e), "executable_path": str(SERVICE_EXECUTABLE)}


async def search_files(
    pattern: str,
    directory: str = ".",
    max_results: int = 100,
    pagination_mode: str | None = None,
    page: int = 1,
    page_size: int = 1000,
) -> dict[str, Any]:
    """Search for files using the FastSearch C++ service via direct NTFS MFT access.

    This function REQUIRES the FastSearch service to be running. It does NOT fall back
    to treewalking as that violates the architecture (direct MFT access only).

    Args:
        pattern: Search pattern (glob or regex)
        directory: Directory to search in
        max_results: Maximum number of results (0 = unlimited, capped at 10M)
        pagination_mode: Pagination mode - "offset" for page-based, None for all results
        page: Page number (1-indexed) for offset pagination
        page_size: Results per page for offset pagination

    Returns:
        Dictionary containing:
            - results: List of file information dictionaries
            - count: Number of results
            - pagination: Pagination metadata (if pagination_mode="offset") or None

    Raises:
        RuntimeError: If the service is not available (no fallback to treewalk)
    """
    try:
        # Check if service is running; attempt auto-start if disconnected
        if not is_service_running():
            logger.info("Service disconnected during search_files; attempting auto-start...")
            from .service_ensure import ensure_service_available

            ensured = await ensure_service_available(start_if_needed=True)
            if not ensured.get("success") and not is_service_running():
                error_msg = (
                    "❌ FastSearch service is not running and could not be started automatically.\n\n"
                    "The FastSearch MCP requires the FastSearch Windows service or standalone engine to be "
                    "running for direct NTFS MFT access.\n\n"
                    "To fix this:\n"
                    "1. Use 'start_service' or run `FastSearchServiceNew.exe --standalone` in terminal\n"
                    "2. Check service status using the 'service_status' tool"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)

        # Try to communicate with the service via named pipe
        try:
            logger.info(f"Searching via NTFS MFT: pattern='{pattern}', directory='{directory}'")
            result = await search_files_via_pipe(
                pattern, directory, max_results, pagination_mode=pagination_mode, page=page, page_size=page_size
            )
            if result is None:
                error_msg = "No response from FastSearch service."
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            if result.get("error"):
                error_msg = result.get("error", "Search failed")
                logger.error(f"MFT search error: {error_msg}")
                raise RuntimeError(error_msg)
            if result.get("results") is not None:
                logger.info(f"MFT search completed: {result.get('count', 0)} files found")
                return result
            else:
                error_msg = (
                    "❌ No response from FastSearch service.\n\n"
                    "The FastSearch service appears to be running but is not "
                    "responding to requests. This may indicate the service is hung "
                    "or experiencing issues.\n\n"
                    "To troubleshoot:\n"
                    "1. Check service status using the 'service_status' tool\n"
                    "2. Try restarting the service: Use 'restart_service' tool "
                    "or Windows Services\n"
                    "3. Check service logs: Use 'get_service_logs' tool\n"
                    "4. If the issue persists, restart the service manually "
                    "as administrator"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        except RuntimeError:
            # Re-raise RuntimeError (our own errors)
            raise
        except Exception as e:
            error_msg = (
                f"❌ Named pipe communication failed: {e}\n\n"
                "The FastSearch service could not be reached via the named pipe. "
                "This usually means:\n"
                "- The service is not running (check with 'service_status' tool)\n"
                "- The service is hung or crashed (try restarting it)\n"
                "- Permission issues (ensure service is running as LocalSystem)\n\n"
                "To fix:\n"
                "1. Check service status: Use 'service_status' tool\n"
                "2. Restart the service: Use 'restart_service' tool or Windows Services\n"
                "3. Check service logs: Use 'get_service_logs' tool for error details"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    except RuntimeError:
        # Re-raise our errors
        raise
    except Exception as e:
        error_msg = f"File search failed: {e}. Service may not be available."
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def start_service_with_details() -> dict[str, Any]:
    """Start the elevated FastSearch Windows Service with comprehensive logging and diagnostics.

    Returns:
        dict: Detailed result containing success status, exit codes, stderr, and Event Log entries.
    """
    global _service_status_cache

    diagnostics: dict[str, Any] = {
        "success": False,
        "installed": True,
        "executable_exists": SERVICE_EXECUTABLE.exists(),
        "executable_path": str(SERVICE_EXECUTABLE),
        "service_name": SERVICE_NAME,
        "logs": [],
    }

    if not SERVICE_EXECUTABLE.exists():
        msg = f"Service binary missing: {SERVICE_EXECUTABLE}"
        logger.error(msg)
        diagnostics["error"] = msg
        diagnostics["logs"].append(f"[ERROR] {msg}")
        return diagnostics

    # 1. Query Windows SCM for service registration status
    scm_check = await asyncio.to_thread(
        subprocess.run, ["sc", "query", SERVICE_NAME], capture_output=True, text=True, timeout=5
    )

    if scm_check.returncode == 1060 or "1060" in scm_check.stderr or "1060" in scm_check.stdout:
        diagnostics["installed"] = False
        msg = f"Service '{SERVICE_NAME}' is not registered in Windows Service Control Manager (Error 1060)."
        logger.warning(msg)
        diagnostics["logs"].append(f"[WARNING] {msg}")
        diagnostics["logs"].append("[UAC] Triggering elevated installation prompt: FastSearchServiceNew.exe install...")

        # Automatic installation via UAC prompt
        install_cmd = f"Start-Process '{SERVICE_EXECUTABLE}' -ArgumentList 'install' -Verb RunAs -Wait; Start-Service {SERVICE_NAME} -ErrorAction SilentlyContinue"
        install_res = await asyncio.to_thread(
            subprocess.run,
            ["powershell.exe", "-NoProfile", "-Command", install_cmd],
            capture_output=True,
            text=True,
            timeout=45,
        )
        diagnostics["logs"].append(f"[UAC Output] ExitCode: {install_res.returncode}")
        if install_res.stderr:
            diagnostics["logs"].append(f"[UAC Stderr] {install_res.stderr.strip()}")

        await asyncio.sleep(2.0)
        if is_service_running():
            _service_status_cache = None
            diagnostics["success"] = True
            diagnostics["installed"] = True
            diagnostics["logs"].append("[SUCCESS] Service installed and started successfully via UAC elevation.")
            return diagnostics

    # 2. Try standard sc start
    sc_start = await asyncio.to_thread(
        subprocess.run, ["sc", "start", SERVICE_NAME], capture_output=True, text=True, timeout=10
    )
    diagnostics["logs"].append(f"[SCM Start] ExitCode: {sc_start.returncode}")
    if sc_start.stdout:
        diagnostics["logs"].append(f"[SCM Stdout] {sc_start.stdout.strip()}")
    if sc_start.stderr:
        diagnostics["logs"].append(f"[SCM Stderr] {sc_start.stderr.strip()}")

    if sc_start.returncode == 0:
        _service_status_cache = None
        diagnostics["success"] = True
        diagnostics["logs"].append("[SUCCESS] Service started successfully via SCM.")
        return diagnostics

    # 3. Trigger UAC elevated start if SCM start returned access denied or failed
    logger.info("SCM start returned code %d; prompting for UAC elevation...", sc_start.returncode)
    ps_cmd = (
        f"Start-Process powershell -ArgumentList '-NoProfile -Command Start-Service {SERVICE_NAME}' -Verb RunAs -Wait"
    )
    uac_res = await asyncio.to_thread(
        subprocess.run,
        ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
        capture_output=True,
        text=True,
        timeout=30,
    )
    diagnostics["logs"].append(f"[UAC Start Output] ExitCode: {uac_res.returncode}")

    await asyncio.sleep(1.5)
    if is_service_running():
        _service_status_cache = None
        diagnostics["success"] = True
        diagnostics["logs"].append("[SUCCESS] Service started successfully after UAC elevation.")
        return diagnostics

    # 4. Fetch recent Windows Event Log entries for FastSearchMCP source to extract exact error trace
    try:
        evt_cmd = f"Get-WinEvent -ProviderName '{SERVICE_NAME}' -MaxEvents 5 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Message"
        evt_res = await asyncio.to_thread(
            subprocess.run,
            ["powershell.exe", "-NoProfile", "-Command", evt_cmd],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if evt_res.stdout.strip():
            diagnostics["event_logs"] = [line.strip() for line in evt_res.stdout.strip().splitlines() if line.strip()]
            diagnostics["logs"].append(f"[EventLog] {evt_res.stdout.strip()}")
    except Exception as e:
        logger.debug("Failed to query EventLog: %s", e)

    # 5. Fallback: Launch in standalone background mode if SCM / UAC service start didn't connect
    if not is_service_running() and SERVICE_EXECUTABLE.exists():
        logger.info("Service SCM start unavailable; launching FastSearch engine in standalone background mode...")
        try:
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
            subprocess.Popen(
                [str(SERVICE_EXECUTABLE), "--standalone"],
                creationflags=creation_flags,
                close_fds=True,
            )
            await asyncio.sleep(1.0)
            if is_service_running():
                _service_status_cache = None
                diagnostics["success"] = True
                diagnostics["logs"].append(
                    "[SUCCESS] FastSearch Engine started successfully in standalone background mode."
                )
                return diagnostics
        except Exception as standalone_err:
            diagnostics["logs"].append(f"[Standalone Error] {standalone_err}")

    diagnostics["error"] = diagnostics["logs"][-1] if diagnostics["logs"] else "Service start failed"
    return diagnostics


async def start_service() -> bool:
    """Start the FastSearch C++ service (returns bool for backward compatibility)."""
    res = await start_service_with_details()
    return res.get("success", False)


async def get_recent_service_logs() -> list[str]:
    """Retrieve recent Windows Event Log entries and runtime traces for FastSearchMCP service."""
    logs: list[str] = []
    try:
        evt_cmd = f"Get-WinEvent -ProviderName '{SERVICE_NAME}' -MaxEvents 15 -ErrorAction SilentlyContinue | Format-Table -AutoSize TimeCreated, Id, LevelDisplayName, Message | Out-String"
        evt_res = await asyncio.to_thread(
            subprocess.run,
            ["powershell.exe", "-NoProfile", "-Command", evt_cmd],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if evt_res.stdout.strip():
            logs.extend(evt_res.stdout.strip().splitlines())
    except Exception as e:
        logger.debug("Failed to fetch Windows Event Log: %s", e)
    return logs


async def stop_service() -> bool:
    """Stop the FastSearch C++ service.

    Returns:
        bool: True if service stopped successfully, False otherwise
    """
    try:
        # Try to stop the service using sc.exe
        result = await asyncio.to_thread(
            subprocess.run, ["sc", "stop", SERVICE_NAME], capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            logger.info("FastSearch service stopped successfully")
            return True
        else:
            logger.error(f"Failed to stop service: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error stopping service: {e}")
        return False


async def test_service_connection() -> dict[str, Any]:
    """Test the connection to the FastSearch service.

    Returns:
        Dict containing connection test results
    """
    try:
        # Check if service is running
        running = is_service_running()

        # Test named pipe connection
        pipe_connected = False
        if running:
            pipe_connected = await test_pipe_connection()

        return {
            "service_running": running,
            "pipe_connected": pipe_connected,
            "executable_exists": SERVICE_EXECUTABLE.exists(),
            "executable_path": str(SERVICE_EXECUTABLE),
            "pipe_name": get_pipe_name(),
        }

    except Exception as e:
        logger.error(f"Service connection test failed: {e}")
        return {"service_running": False, "pipe_connected": False, "error": str(e)}
