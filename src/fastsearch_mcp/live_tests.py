"""
Live integration tests: pipe connection and real searches via the FastSearch C++ service.

Used by the webapp Tests page and can be run from pytest with the service running.
"""

import logging
import time
from typing import Any

from .pipe_client import (
    get_pipe_name,
    get_service_info_via_pipe,
    search_files_via_pipe,
    test_pipe_connection_with_diagnostics,
)
from .service_client import is_service_running

logger = logging.getLogger(__name__)


def _record(name: str, passed: bool, message: str, duration_ms: float, details: Any = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": name,
        "passed": passed,
        "message": message,
        "duration_ms": round(duration_ms, 2),
    }
    if details is not None:
        out["details"] = details
    return out


async def run_live_tests(
    search_pattern: str = "*.txt",
    search_directory: str = "C:\\",
    search_max_results: int = 5,
) -> list[dict[str, Any]]:
    """Run live tests: service check, pipe connect, get_service_info, real search.

    Args:
        search_pattern: Glob pattern for the real search test (default: *.txt).
        search_directory: Directory for the real search test (default: C:\\).
        search_max_results: Max results for the real search test (default: 5).

    Returns:
        List of test result dicts: name, passed, message, duration_ms, details (optional).
    """
    results: list[dict[str, Any]] = []

    # 1. Service process check (fast, cached)
    t0 = time.perf_counter()
    try:
        running = is_service_running()
        elapsed = (time.perf_counter() - t0) * 1000
        results.append(
            _record(
                "service_process",
                running,
                "Service process is running" if running else "Service process not running (pipe or tasklist)",
                elapsed,
                {"running": running},
            )
        )
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.exception("service_process test failed")
        results.append(_record("service_process", False, str(e), elapsed, {"error": str(e)}))

    # 2. Pipe connection (ping) with diagnostics
    t0 = time.perf_counter()
    try:
        diag = await test_pipe_connection_with_diagnostics()
        elapsed = (time.perf_counter() - t0) * 1000
        connected = bool(diag.get("connected") and diag.get("ping_ok"))
        if connected:
            msg = "Named pipe connected and ping OK"
        else:
            err_code = diag.get("error_code")
            err_msg = diag.get("error_message") or "Unknown"
            pipe_used = diag.get("pipe_name", get_pipe_name())
            if err_code == 2:
                msg = (
                    f"Named pipe not found (error 2). Service may not create {pipe_used}. "
                    "Set FASTSEARCH_PIPE_NAME to match your service, or ensure the FastSearch service is running."
                )
            elif err_code == 5:
                msg = f"Access denied (error 5) connecting to {pipe_used}. Run as same user as service or check pipe ACLs."
            else:
                msg = f"Pipe not available or ping failed: {err_msg}"
        results.append(_record("pipe_connect", connected, msg, elapsed, diag))
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.exception("pipe_connect test failed")
        results.append(_record("pipe_connect", False, str(e), elapsed, {"error": str(e)}))

    # 3. Get service info via pipe (only if pipe connected)
    if results[-1].get("passed"):
        t0 = time.perf_counter()
        try:
            info = await get_service_info_via_pipe()
            elapsed = (time.perf_counter() - t0) * 1000
            results.append(
                _record(
                    "get_service_info",
                    info is not None,
                    "Got service info via pipe" if info else "get_service_info returned None",
                    elapsed,
                    info if info else None,
                )
            )
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.exception("get_service_info test failed")
            results.append(_record("get_service_info", False, str(e), elapsed, {"error": str(e)}))
    else:
        results.append(_record("get_service_info", False, "Skipped (pipe not connected)", 0.0, {"skipped": True}))

    # 4. Real search via pipe
    if results[1].get("passed"):  # pipe_connect passed
        t0 = time.perf_counter()
        try:
            search_result = await search_files_via_pipe(
                pattern=search_pattern,
                directory=search_directory,
                max_results=search_max_results,
                timeout=30.0,
            )
            elapsed = (time.perf_counter() - t0) * 1000
            err = search_result.get("error")
            if err:
                results.append(
                    _record(
                        "search_via_pipe",
                        False,
                        f"Search returned error: {err}",
                        elapsed,
                        {"error": err, "pattern": search_pattern, "directory": search_directory},
                    )
                )
            else:
                count = search_result.get("count", 0)
                result_list = search_result.get("results") or []
                results.append(
                    _record(
                        "search_via_pipe",
                        True,
                        f"Search OK: {count} result(s) for {search_pattern!r} in {search_directory!r}",
                        elapsed,
                        {
                            "pattern": search_pattern,
                            "directory": search_directory,
                            "count": count,
                            "sample_paths": [r.get("path") for r in result_list[:3]] if result_list else [],
                        },
                    )
                )
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.exception("search_via_pipe test failed")
            results.append(
                _record(
                    "search_via_pipe",
                    False,
                    str(e),
                    elapsed,
                    {"error": str(e), "pattern": search_pattern, "directory": search_directory},
                )
            )
    else:
        results.append(
            _record(
                "search_via_pipe",
                False,
                "Skipped (pipe not connected)",
                0.0,
                {"skipped": True, "pattern": search_pattern, "directory": search_directory},
            )
        )

    return results
