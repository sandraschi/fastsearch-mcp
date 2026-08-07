#!/usr/bin/env python3
"""Test script for FastSearch NTFS tools."""

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
    result_file = os.path.join(os.path.dirname(script), "test_ntfs_results.txt")
    " ".join([f'"{arg}"' for arg in sys.argv[1:]])

    try:
        # Request elevation - redirect output to file so we can read it back
        import subprocess

        subprocess.Popen(
            [sys.executable, script, "--elevated", "--result-file", result_file],
            shell=True,
            creationflags=0x08000000,  # CREATE_NO_WINDOW - but this won't work with UAC
        )
        print(f"\nUAC elevation requested. Results will be written to: {result_file}")
        print("Please approve the UAC prompt, then check the result file.")
        return True  # Elevation requested
    except Exception:
        # Fallback to ShellExecuteW - use SW_SHOW to keep window visible
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # Request elevation
                sys.executable,
                f'"{script}" --elevated --result-file "{result_file}"',
                None,
                5,  # SW_SHOW - show window and activate it
            )
            print("\nUAC elevation requested. A new window will open and stay open.")
            print(f"Results will also be written to: {result_file}")
            return True
        except Exception as e2:
            print(f"Failed to request elevation: {e2}")
            print("Please run this script as Administrator")
            return False


# Import directly from ntfs module to avoid importing all tools
from fastsearch_mcp.tools.ntfs import (
    ntfs_check_health,
    ntfs_list_volumes,
    ntfs_volume_info,
)


class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []

    def add_pass(self, test_name: str, duration: float, details: str = ""):
        self.passed.append((test_name, duration, details))
        print(f"[PASS] {test_name} ({duration * 1000:.1f}ms) {details}")

    def add_fail(self, test_name: str, error: str, duration: float):
        self.failed.append((test_name, error, duration))
        print(f"[FAIL] {test_name} ({duration * 1000:.1f}ms) - {error}")

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
                print(f"  ✓ {name} ({duration * 1000:.1f}ms) {details}")
            print()

        if self.failed:
            print("FAILED TESTS:")
            for name, error, duration in self.failed:
                print(f"  ✗ {name} ({duration * 1000:.1f}ms)")
                print(f"    Error: {error}")
            print()

        if self.skipped:
            print("SKIPPED TESTS:")
            for name, reason in self.skipped:
                print(f"  ⊘ {name}: {reason}")
            print()


results = TestResults()


async def test_ntfs_list_volumes():
    """Test listing all NTFS volumes."""
    test_name = "NTFS List Volumes"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        result = await (ntfs_list_volumes.fn if hasattr(ntfs_list_volumes, "fn") else ntfs_list_volumes)()
        duration = time.time() - start

        if isinstance(result, list) and len(result) > 0:
            volume_count = len(result)
            volume_names = [v.get("device", "unknown") for v in result[:3]]
            details = f"Found {volume_count} NTFS volume(s): {', '.join(volume_names)}"
            if volume_count > 3:
                details += "..."
            results.add_pass(test_name, duration, details)
            return True
        else:
            results.add_fail(test_name, f"Expected list of volumes, got: {result}", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_ntfs_volume_info():
    """Test getting volume info for C: drive."""
    test_name = "NTFS Volume Info - C:"
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
        result = await (ntfs_volume_info.fn if hasattr(ntfs_volume_info, "fn") else ntfs_volume_info)("C:")
        duration = time.time() - start

        if result.get("volume_path"):
            total_gb = result.get("total_bytes", 0) / (1024**3)
            free_gb = result.get("free_bytes", 0) / (1024**3)
            used_pct = result.get("used_percent", 0)
            details = f"Total: {total_gb:.1f}GB, Free: {free_gb:.1f}GB, Used: {used_pct:.1f}%"
            results.add_pass(test_name, duration, details)
            return True
        else:
            results.add_fail(test_name, f"Invalid response: {result}", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        error_msg = str(e)
        if "Access is denied" in error_msg or "privileges" in error_msg:
            results.add_skip(test_name, "Access denied - may need administrator privileges")
            return True
        results.add_fail(test_name, error_msg, duration)
        return False


async def test_ntfs_volume_info_drive():
    """Test getting volume info for D: drive."""
    test_name = "NTFS Volume Info - D:"
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
        result = await (ntfs_volume_info.fn if hasattr(ntfs_volume_info, "fn") else ntfs_volume_info)("D:")
        duration = time.time() - start

        if result.get("volume_path"):
            total_gb = result.get("total_bytes", 0) / (1024**3)
            free_gb = result.get("free_bytes", 0) / (1024**3)
            used_pct = result.get("used_percent", 0)
            details = f"Total: {total_gb:.1f}GB, Free: {free_gb:.1f}GB, Used: {used_pct:.1f}%"
            results.add_pass(test_name, duration, details)
            return True
        else:
            results.add_fail(test_name, f"Invalid response: {result}", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        error_msg = str(e)
        if "Access is denied" in error_msg or "privileges" in error_msg:
            results.add_skip(test_name, "Access denied - may need administrator privileges")
            return True
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            results.add_skip(test_name, "D: drive not available")
            return True
        results.add_fail(test_name, error_msg, duration)
        return False


async def test_ntfs_check_health():
    """Test checking volume health for C: drive."""
    test_name = "NTFS Check Health - C:"
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
        result = await (ntfs_check_health.fn if hasattr(ntfs_check_health, "fn") else ntfs_check_health)("C:")
        duration = time.time() - start

        if result.get("health_score") is not None:
            health_score = result.get("health_score", 0)
            health_status = result.get("health_status", "unknown")
            details = f"Health score: {health_score}/100 ({health_status})"
            results.add_pass(test_name, duration, details)
            return True
        else:
            results.add_fail(test_name, f"Invalid response: {result}", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        error_msg = str(e)
        if "Access is denied" in error_msg or "privileges" in error_msg:
            results.add_skip(test_name, "Access denied - may need administrator privileges")
            return True
        results.add_fail(test_name, error_msg, duration)
        return False


async def main():
    """Run all NTFS tool tests."""
    # Check for elevated mode and result file
    result_file = None
    if "--elevated" in sys.argv:
        idx = sys.argv.index("--result-file")
        if idx + 1 < len(sys.argv):
            result_file = sys.argv[idx + 1]

    print("=" * 80)
    print("FASTSEARCH NTFS TOOLS TEST")
    if is_admin():
        print("(Running with Administrator privileges)")
    print("=" * 80)
    print()

    tests = [
        ("NTFS List Volumes", test_ntfs_list_volumes, False),
        ("NTFS Volume Info - C:", test_ntfs_volume_info, False),
        ("NTFS Volume Info - D:", test_ntfs_volume_info_drive, False),
        ("NTFS Check Health - C:", test_ntfs_check_health, False),
    ]

    print("RUNNING TESTS")
    print("=" * 80)

    for test_name, test_func, _ in tests:
        try:
            await test_func()
        except Exception as e:
            results.add_fail(test_name, f"Unexpected error: {e}", 0.0)

    # Print summary
    summary = []
    summary.append("=" * 80)
    summary.append("TEST SUMMARY")
    summary.append("=" * 80)
    summary.append(f"Passed: {len(results.passed)}")
    summary.append(f"Failed: {len(results.failed)}")
    summary.append(f"Skipped: {len(results.skipped)}")
    summary.append("")

    if results.passed:
        summary.append("PASSED TESTS:")
        for name, duration, details in results.passed:
            summary.append(f"  ✓ {name} ({duration * 1000:.1f}ms) {details}")
        summary.append("")

    if results.failed:
        summary.append("FAILED TESTS:")
        for name, error, duration in results.failed:
            summary.append(f"  ✗ {name} ({duration * 1000:.1f}ms)")
            summary.append(f"    Error: {error}")
        summary.append("")

    if results.skipped:
        summary.append("SKIPPED TESTS:")
        for name, reason in results.skipped:
            summary.append(f"  ⊘ {name}: {reason}")
        summary.append("")

    summary_text = "\n".join(summary)
    print(summary_text)

    # Write to result file if specified
    if result_file:
        try:
            with open(result_file, "w", encoding="utf-8") as f:
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
