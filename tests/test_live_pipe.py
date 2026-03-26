"""
Live integration tests: real pipe connection and real search via FastSearch C++ service.

Run with the FastSearch Windows service installed and running:
  pytest tests/test_live_pipe.py -v
  pytest tests/test_live_pipe.py -v -m "service"
Skip when service is not available:
  pytest -m "not service"
"""

import sys

import pytest

from fastsearch_mcp.live_tests import run_live_tests


@pytest.mark.integration
@pytest.mark.service
@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform != "win32", reason="FastSearch service is Windows-only")
async def test_live_pipe_and_search() -> None:
    """Run full live test suite: service check, pipe connect, get_service_info, real search."""
    results = await run_live_tests(
        search_pattern="*.txt",
        search_directory="C:\\",
        search_max_results=5,
    )
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    failed = [r for r in results if not r.get("passed")]
    assert total > 0, "run_live_tests should return at least one result"
    assert passed == total, (
        f"Expected all {total} tests to pass; failed: {[f['name'] for f in failed]}. "
        f"Details: {failed}"
    )


@pytest.mark.integration
@pytest.mark.service
@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform != "win32", reason="FastSearch service is Windows-only")
async def test_live_search_via_pipe_custom_params() -> None:
    """Run live tests with custom pattern/directory to exercise search_via_pipe."""
    results = await run_live_tests(
        search_pattern="*.py",
        search_directory="C:\\",
        search_max_results=3,
    )
    # At least search_via_pipe should be present
    names = [r["name"] for r in results]
    assert "search_via_pipe" in names
    # search_via_pipe result should have passed and message
    search_result = next((r for r in results if r["name"] == "search_via_pipe"), None)
    assert search_result is not None
    assert "passed" in search_result
    assert "message" in search_result
