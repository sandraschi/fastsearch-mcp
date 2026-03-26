#!/usr/bin/env python3
"""Test script for FastSearch service management tools."""
import asyncio
import ctypes
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def is_admin():
    """Check if running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False


def elevate_if_needed():
    """Request UAC elevation if not running as admin."""
    if is_admin():
        return False  # Already admin, no need to elevate

    # Re-run the program with admin rights
    script = os.path.abspath(__file__)
    result_file = os.path.join(os.path.dirname(script), "test_service_results.txt")

    try:
        # Request elevation - use SW_SHOW to keep window visible
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",  # Request elevation
            sys.executable,
            f'"{script}" --elevated --result-file "{result_file}"',
            None,
            5  # SW_SHOW - show window and activate it
        )
        print("\nUAC elevation requested. A new window will open and stay open.")
        print(f"Results will also be written to: {result_file}")
        return True  # Elevation requested
    except Exception as e:
        print(f"Failed to request elevation: {e}")
        print("Please run this script as Administrator")
        return False

# Import directly from service module to avoid importing all tools
from fastsearch_mcp.tools.service import (
    service_repair_fastsearch,
    service_restart_fastsearch,
    service_start_fastsearch,
    service_status_fastsearch,
    service_stop_fastsearch,
)


class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []

    def add_pass(self, test_name: str, duration: float, details: str = ""):
        self.passed.append((test_name, duration, details))
        print(f"[PASS] {test_name} ({duration*1000:.1f}ms) {details}")

    def add_fail(self, test_name: str, error: str, duration: float):
        self.failed.append((test_name, error, duration))
        print(f"[FAIL] {test_name} ({duration*1000:.1f}ms) - {error}")

    def add_skip(self, test_name: str, reason: str):
        self.skipped.append((test_name, reason))
        print(f"[SKIP] {test_name} - {reason}")

    def print_summary(self):
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        print(f"Skipped: {len(self.skipped)}")
        print()

        if self.passed:
            print("PASSED TESTS:")
            for name, duration, details in self.passed:
                print(f"  ✓ {name} ({duration*1000:.1f}ms) {details}")
            print()

        if self.failed:
            print("FAILED TESTS:")
            for name, error, duration in self.failed:
                print(f"  ✗ {name} ({duration*1000:.1f}ms)")
                print(f"    Error: {error}")
            print()

        if self.skipped:
            print("SKIPPED TESTS:")
            for name, reason in self.skipped:
                print(f"  ⊘ {name}: {reason}")
            print()


results = TestResults()


async def test_service_status():
    """Test getting service status."""
    test_name = "Service Status"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        result = await (service_status_fastsearch.fn if hasattr(service_status_fastsearch, "fn") else service_status_fastsearch)()
        duration = time.time() - start

        status = result.get("status")
        if status:
            details = f"Status: {status}"
            if "pid" in result and result["pid"]:
                details += f", PID: {result['pid']}"
            results.add_pass(test_name, duration, details)
            return True
        else:
            results.add_fail(test_name, f"Invalid response: {result}", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_service_start():
    """Test starting the service."""
    test_name = "Service Start"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()

    if not is_admin():
        if elevate_if_needed():
            results.add_skip(test_name, "Requested UAC elevation - please approve and re-run")
            return True
        else:
            results.add_skip(test_name, "Requires administrator privileges")
            return True

    start = time.time()
    try:
        # Check current status first
        status_result = await (service_status_fastsearch.fn if hasattr(service_status_fastsearch, "fn") else service_status_fastsearch)()
        current_status = status_result.get("status")

        if current_status == "running":
            results.add_skip(test_name, "Service already running")
            return True

        result = await (service_start_fastsearch.fn if hasattr(service_start_fastsearch, "fn") else service_start_fastsearch)()
        duration = time.time() - start

        if result.get("success"):
            # Wait a moment and verify it's running
            await asyncio.sleep(1)
            status_result = await (service_status_fastsearch.fn if hasattr(service_status_fastsearch, "fn") else service_status_fastsearch)()
            if status_result.get("status") == "running":
                results.add_pass(test_name, duration, "Service started successfully")
                return True
            else:
                results.add_fail(
                    test_name,
                    f"Service start reported success but status is {status_result.get('status')}",
                    duration,
                )
                return False
        else:
            results.add_fail(test_name, f"Start failed: {result}", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        error_msg = str(e)
        if "Administrator" in error_msg or "privileges" in error_msg:
            results.add_skip(test_name, "Requires administrator privileges")
            return True
        results.add_fail(test_name, error_msg, duration)
        return False


async def test_service_stop():
    """Test stopping the service."""
    test_name = "Service Stop"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()

    if not is_admin():
        if elevate_if_needed():
            results.add_skip(test_name, "Requested UAC elevation - please approve and re-run")
            return True
        else:
            results.add_skip(test_name, "Requires administrator privileges")
            return True

    start = time.time()
    try:
        # Check current status first
        status_result = await (service_status_fastsearch.fn if hasattr(service_status_fastsearch, "fn") else service_status_fastsearch)()
        current_status = status_result.get("status")

        if current_status == "stopped" or current_status == "not_installed":
            results.add_skip(test_name, f"Service is {current_status}")
            return True

        result = await (service_stop_fastsearch.fn if hasattr(service_stop_fastsearch, "fn") else service_stop_fastsearch)()
        duration = time.time() - start

        if result.get("success"):
            # Wait a moment and verify it's stopped
            await asyncio.sleep(1)
            status_result = await (service_status_fastsearch.fn if hasattr(service_status_fastsearch, "fn") else service_status_fastsearch)()
            if status_result.get("status") == "stopped":
                results.add_pass(test_name, duration, "Service stopped successfully")
                return True
            else:
                results.add_fail(
                    test_name,
                    f"Service stop reported success but status is {status_result.get('status')}",
                    duration,
                )
                return False
        else:
            results.add_fail(test_name, f"Stop failed: {result}", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        error_msg = str(e)
        if "Administrator" in error_msg or "privileges" in error_msg:
            results.add_skip(test_name, "Requires administrator privileges")
            return True
        results.add_fail(test_name, error_msg, duration)
        return False


async def test_service_restart():
    """Test restarting the service."""
    test_name = "Service Restart"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()

    if not is_admin():
        if elevate_if_needed():
            results.add_skip(test_name, "Requested UAC elevation - please approve and re-run")
            return True
        else:
            results.add_skip(test_name, "Requires administrator privileges")
            return True

    start = time.time()
    try:
        # Get initial status
        initial_status = await (service_status_fastsearch.fn if hasattr(service_status_fastsearch, "fn") else service_status_fastsearch)()
        initial_state = initial_status.get("status")

        if initial_state == "not_installed":
            results.add_skip(test_name, "Service not installed")
            return True

        result = await (service_restart_fastsearch.fn if hasattr(service_restart_fastsearch, "fn") else service_restart_fastsearch)()
        duration = time.time() - start

        if result.get("success"):
            # Wait a moment and verify it's running
            await asyncio.sleep(2)
            status_result = await (service_status_fastsearch.fn if hasattr(service_status_fastsearch, "fn") else service_status_fastsearch)()
            if status_result.get("status") == "running":
                results.add_pass(test_name, duration, "Service restarted successfully")
                return True
            else:
                results.add_fail(
                    test_name,
                    f"Service restart reported success but status is {status_result.get('status')}",
                    duration,
                )
                return False
        else:
            results.add_fail(test_name, f"Restart failed: {result}", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        error_msg = str(e)
        if "Administrator" in error_msg or "privileges" in error_msg:
            results.add_skip(test_name, "Requires administrator privileges")
            return True
        results.add_fail(test_name, error_msg, duration)
        return False


async def test_service_repair():
    """Test repairing the service."""
    test_name = "Service Repair"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()

    if not is_admin():
        if elevate_if_needed():
            results.add_skip(test_name, "Requested UAC elevation - please approve and re-run")
            return True
        else:
            results.add_skip(test_name, "Requires administrator privileges")
            return True

    start = time.time()
    try:
        result = await (service_repair_fastsearch.fn if hasattr(service_repair_fastsearch, "fn") else service_repair_fastsearch)()
        duration = time.time() - start

        if result.get("success"):
            results.add_pass(test_name, duration, result.get("message", "Service repaired"))
            return True
        else:
            results.add_fail(test_name, f"Repair failed: {result}", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        error_msg = str(e)
        if "Administrator" in error_msg or "privileges" in error_msg:
            results.add_skip(test_name, "Requires administrator privileges")
            return True
        results.add_fail(test_name, error_msg, duration)
        return False


async def main():
    """Run all service tool tests."""
    # Check for elevated mode and result file
    result_file = None
    if "--elevated" in sys.argv:
        try:
            idx = sys.argv.index("--result-file")
            if idx + 1 < len(sys.argv):
                result_file = sys.argv[idx + 1]
        except ValueError:
            pass

    print("=" * 80)
    print("FASTSEARCH SERVICE TOOLS TEST")
    if is_admin():
        print("(Running with Administrator privileges)")
    print("=" * 80)
    print()

    # Test order matters - status first, then control operations
    tests = [
        ("Service Status", test_service_status, False),
        ("Service Start", test_service_start, False),
        ("Service Stop", test_service_stop, False),
        ("Service Restart", test_service_restart, False),
        ("Service Repair", test_service_repair, False),
    ]

    print("RUNNING TESTS")
    print("=" * 80)

    for test_name, test_func, _ in tests:
        try:
            await test_func()
        except Exception as e:
            results.add_fail(test_name, f"Unexpected error: {e}", 0.0)

    # Get summary text
    summary_lines = []
    summary_lines.append("=" * 80)
    summary_lines.append("TEST SUMMARY")
    summary_lines.append("=" * 80)
    summary_lines.append(f"Passed: {len(results.passed)}")
    summary_lines.append(f"Failed: {len(results.failed)}")
    summary_lines.append(f"Skipped: {len(results.skipped)}")
    summary_lines.append("")

    if results.passed:
        summary_lines.append("PASSED TESTS:")
        for name, duration, details in results.passed:
            summary_lines.append(f"  ✓ {name} ({duration*1000:.1f}ms) {details}")
        summary_lines.append("")

    if results.failed:
        summary_lines.append("FAILED TESTS:")
        for name, error, duration in results.failed:
            summary_lines.append(f"  ✗ {name} ({duration*1000:.1f}ms)")
            summary_lines.append(f"    Error: {error}")
        summary_lines.append("")

    if results.skipped:
        summary_lines.append("SKIPPED TESTS:")
        for name, reason in results.skipped:
            summary_lines.append(f"  ⊘ {name}: {reason}")
        summary_lines.append("")

    summary_text = "\n".join(summary_lines)
    print(summary_text)

    # Write to result file if specified
    if result_file:
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(summary_text)
            print(f"\nResults written to: {result_file}")
        except Exception as e:
            print(f"\nWarning: Could not write results to file: {e}")

    # If running elevated, add a small delay so user can see results, then exit
    if "--elevated" in sys.argv:
        print("\n" + "=" * 80)
        print("Tests completed. Window will close in 5 seconds...")
        print("=" * 80)
        import time
        time.sleep(5)

    # Exit with error code if any tests failed
    if results.failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

