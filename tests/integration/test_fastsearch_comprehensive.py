#!/usr/bin/env python3
"""
Comprehensive test harness for FastSearch MCP tools.

Tests all FastSearch tools with extensive coverage:
- File name pattern searches
- Size and date range filters
- Multi-drive and all-drive searches
- Speed measurements
- Service management
- Disk analysis
- And more
"""

import asyncio
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.service_client import test_service_connection as check_service_connection
from fastsearch_mcp.tools import (
    analyze_disk_usage,
    drive_inventory,
    fastsearch_search,
    fastsearch_search_advanced,
    help,
    ntfs_volume_info,
    service_status,
)


class TestResults:
    """Track test results."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors: List[Dict[str, Any]] = []
        self.total_tests = 0
        self.completed_tests = 0

    def set_total(self, total: int):
        """Set total number of tests."""
        self.total_tests = total

    def _get_progress(self) -> str:
        """Get progress indicator."""
        if self.total_tests > 0:
            return f"[{self.completed_tests}/{self.total_tests}]"
        return ""

    def add_pass(self, test_name: str, duration: float, details: str = ""):
        """Record a passed test."""
        self.passed += 1
        self.completed_tests += 1
        progress = self._get_progress()
        duration_ms = duration * 1000
        print(f"{progress} [PASS] {test_name} ({duration_ms:.1f}ms) {details}")
        sys.stdout.flush()

    def add_fail(self, test_name: str, error: str, duration: float = 0):
        """Record a failed test."""
        self.failed += 1
        self.completed_tests += 1
        self.errors.append({"test": test_name, "error": error})
        progress = self._get_progress()
        duration_ms = duration * 1000
        print(f"{progress} [FAIL] {test_name} ({duration_ms:.1f}ms) - {error}")
        sys.stdout.flush()

    def add_skip(self, test_name: str, reason: str):
        """Record a skipped test."""
        self.skipped += 1
        self.completed_tests += 1
        progress = self._get_progress()
        print(f"{progress} [SKIP] {test_name} - {reason}")
        sys.stdout.flush()

    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed + self.skipped
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total: {total}")
        print(f"Passed: {self.passed} [PASS]")
        print(f"Failed: {self.failed} [FAIL]")
        print(f"Skipped: {self.skipped} [SKIP]")
        if self.errors:
            print("\nFAILURES:")
            for err in self.errors:
                print(f"  - {err['test']}: {err['error']}")
        print("=" * 80)


results = TestResults()


async def test_service_connection():
    """Test service connection."""
    test_name = "Service Connection"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        status = await check_service_connection()
        duration = time.time() - start
        if status.get("service_running") and status.get("pipe_connected"):
            results.add_pass(test_name, duration, "Service running and pipe connected")
            return True
        else:
            results.add_fail(
                test_name,
                f"Service not available: {status}",
                duration,
            )
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_basic_search():
    """Test basic file name pattern search."""
    test_name = "Basic Search - *.py"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        # FastMCP tools are awaitable FunctionTool objects
        tool = fastsearch_search
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(pattern="*.py", path="C:\\", max_results=10)
        else:
            result = await tool(pattern="*.py", path="C:\\", max_results=10)
        duration = time.time() - start
        if result.get("success") and result.get("count", 0) > 0:
            results.add_pass(
                test_name,
                duration,
                f"Found {result['count']} files ({duration * 1000:.1f}ms)",
            )
            return True
        else:
            results.add_fail(
                test_name,
                f"No results or failed: {result.get('error', 'Unknown')}",
                duration,
            )
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_cpp_search():
    """Test C++ file search."""
    test_name = "C++ File Search - *.cpp"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = fastsearch_search
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(pattern="*.cpp", path="D:\\", max_results=20)
        else:
            result = await tool(pattern="*.cpp", path="D:\\", max_results=20)
        duration = time.time() - start
        if result.get("success"):
            count = result.get("count", 0)
            if count > 0:
                results.add_pass(
                    test_name,
                    duration,
                    f"Found {count} .cpp files ({duration * 1000:.1f}ms)",
                )
            else:
                results.add_fail(
                    test_name,
                    f"No .cpp files found on D: (expected files exist) - result: {result}",
                    duration,
                )
            return True
        else:
            results.add_fail(
                test_name,
                f"Search failed: {result.get('error', 'Unknown')}",
                duration,
            )
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_d_py_search():
    """Test Python file search on D: drive."""
    test_name = "D: Drive - *.py Search"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = fastsearch_search
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(pattern="*.py", path="D:\\", max_results=20)
        else:
            result = await tool(pattern="*.py", path="D:\\", max_results=20)
        duration = time.time() - start
        if result.get("success"):
            count = result.get("count", 0)
            if count > 0:
                results.add_pass(
                    test_name,
                    duration,
                    f"Found {count} .py files on D: ({duration * 1000:.1f}ms)",
                )
            else:
                results.add_fail(
                    test_name,
                    f"No .py files found on D: - result: {result}",
                    duration,
                )
            return True
        else:
            results.add_fail(
                test_name,
                f"Search failed: {result.get('error', 'Unknown')} - result: {result}",
                duration,
            )
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_extension_lengths():
    """Test pattern matching with different extension lengths to check for extension-length bugs."""
    test_name = "Extension Length Test - Various Extensions"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()

    # Test various extension lengths: 1 char (.c), 2 chars (.py), 3 chars (.cpp), 4 chars (.html)
    extensions = [
        ("*.c", "1-char extension"),
        ("*.py", "2-char extension"),
        ("*.cpp", "3-char extension"),
        ("*.hpp", "3-char extension (header)"),
        ("*.txt", "3-char extension (text)"),
        ("*.html", "4-char extension"),
        ("*.json", "4-char extension"),
    ]

    all_passed = True
    results_summary = []

    try:
        tool = fastsearch_search
        for pattern, desc in extensions:
            try:
                if hasattr(tool, "fn"):
                    result = await (tool.fn if hasattr(tool, "fn") else tool)(pattern=pattern, path="D:\\", max_results=5)
                else:
                    result = await tool(pattern=pattern, path="D:\\", max_results=5)

                if result.get("success"):
                    count = result.get("count", 0)
                    results_summary.append(f"{pattern}: {count} files")
                    if count == 0:
                        # Not necessarily a failure - might not have files of that type
                        results_summary.append(f"  ({desc} - no files found, may be expected)")
                else:
                    results_summary.append(f"{pattern}: FAILED - {result.get('error', 'Unknown')}")
                    all_passed = False
            except Exception as e:
                results_summary.append(f"{pattern}: EXCEPTION - {str(e)}")
                all_passed = False

        duration = time.time() - start
        summary_text = "; ".join(results_summary)

        if all_passed:
            results.add_pass(
                test_name,
                duration,
                f"All extensions tested: {summary_text}",
            )
        else:
            results.add_fail(
                test_name,
                f"Some extensions failed: {summary_text}",
                duration,
            )
        return all_passed
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_search_all_drives():
    """Test searching all NTFS drives."""
    test_name = "Search All Drives - *.txt"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = fastsearch_search
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(pattern="*.txt", search_all=True, max_results=50)
        else:
            result = await tool(pattern="*.txt", search_all=True, max_results=50)
        duration = time.time() - start
        if result.get("success"):
            count = result.get("count", 0)
            drives = result.get("drives_searched", [])
            results.add_pass(
                test_name,
                duration,
                f"Found {count} files across {len(drives)} drives ({duration * 1000:.1f}ms)",
            )
            return True
        else:
            results.add_fail(
                test_name,
                f"Search failed: {result.get('error', 'Unknown')}",
                duration,
            )
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_advanced_search_size_filter():
    """Test advanced search with size filter."""
    test_name = "Advanced Search - Size Filter (>1MB)"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        # Search for files larger than 1MB
        tool = fastsearch_search_advanced
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(
                pattern="*",
                path="C:\\",
                min_size=1024 * 1024,  # 1MB
                max_results=20,
            )
        else:
            result = await tool(
                pattern="*",
                path="C:\\",
                min_size=1024 * 1024,  # 1MB
                max_results=20,
            )
        duration = time.time() - start
        if result.get("success"):
            count = result.get("count", 0)
            results.add_pass(
                test_name,
                duration,
                f"Found {count} files >1MB ({duration * 1000:.1f}ms)",
            )
            return True
        else:
            results.add_fail(
                test_name,
                f"Search failed: {result.get('error', 'Unknown')}",
                duration,
            )
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_advanced_search_date_filter():
    """Test advanced search with date filter."""
    test_name = "Advanced Search - Date Filter (Last 7 Days)"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        # Search for files modified in last 7 days
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        modified_after = int(week_ago.timestamp() * 10000000) + 116444736000000000

        tool = fastsearch_search_advanced
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(
                pattern="*",
                path="C:\\",
                modified_after=modified_after,
                max_results=20,
            )
        else:
            result = await tool(
                pattern="*",
                path="C:\\",
                modified_after=modified_after,
                max_results=20,
            )
        duration = time.time() - start
        if result.get("success"):
            count = result.get("count", 0)
            results.add_pass(
                test_name,
                duration,
                f"Found {count} files modified in last 7 days ({duration * 1000:.1f}ms)",
            )
            return True
        else:
            results.add_fail(
                test_name,
                f"Search failed: {result.get('error', 'Unknown')}",
                duration,
            )
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_advanced_search_combined_filters():
    """Test advanced search with combined filters."""
    test_name = "Advanced Search - Combined Filters (Size + Date)"
    start = time.time()
    try:
        # Search for large files modified recently
        now = datetime.now()
        month_ago = now - timedelta(days=30)
        modified_after = int(month_ago.timestamp() * 10000000) + 116444736000000000

        tool = fastsearch_search_advanced
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(
                pattern="*.exe",
                path="C:\\",
                min_size=1024 * 1024,  # 1MB
                modified_after=modified_after,
                max_results=10,
            )
        else:
            result = await tool(
                pattern="*.exe",
                path="C:\\",
                min_size=1024 * 1024,  # 1MB
                modified_after=modified_after,
                max_results=10,
            )
        duration = time.time() - start
        if result.get("success"):
            count = result.get("count", 0)
            results.add_pass(
                test_name,
                duration,
                f"Found {count} .exe files >1MB modified in last month ({duration * 1000:.1f}ms)",
            )
            return True
        else:
            results.add_fail(
                test_name,
                f"Search failed: {result.get('error', 'Unknown')}",
                duration,
            )
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_speed_benchmark():
    """Benchmark search speed."""
    test_name = "Speed Benchmark - 100 Results"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = fastsearch_search
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(pattern="*.dll", path="C:\\", max_results=100)
        else:
            result = await tool(pattern="*.dll", path="C:\\", max_results=100)
        duration = time.time() - start
        if result.get("success"):
            count = result.get("count", 0)
            speed_ms = duration * 1000
            results_per_sec = count / duration if duration > 0 else 0
            results.add_pass(
                test_name,
                duration,
                f"{count} results in {speed_ms:.1f}ms ({results_per_sec:.0f} results/sec)",
            )
            return True
        else:
            results.add_fail(
                test_name,
                f"Search failed: {result.get('error', 'Unknown')}",
                duration,
            )
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_unlimited_results_performance():
    """Test unlimited results performance over millions of files.
    
    This test searches for common file patterns with unlimited results
    to validate performance on large-scale searches. Tests the core
    value proposition of FastSearch - handling millions of files efficiently.
    """
    test_name = "Unlimited Results Performance - Millions of Files"
    print(f"\n>>> Running: {test_name}...")
    print("   This test may take several minutes on large drives...")
    sys.stdout.flush()
    
    # Test patterns that typically match many files
    test_patterns = [
        ("*.dll", "DLL files (system files)"),
        ("*.exe", "Executable files"),
        ("*.txt", "Text files"),
    ]
    
    # Test on C: drive (typically has most files)
    test_drive = "C:\\"
    
    all_results = []
    
    for pattern, description in test_patterns:
        print(f"\n   Testing: {pattern} ({description})")
        sys.stdout.flush()
        
        start = time.time()
        try:
            tool = fastsearch_search
            if hasattr(tool, "fn"):
                result = await (tool.fn if hasattr(tool, "fn") else tool)(
                    pattern=pattern,
                    path=test_drive,
                    max_results=0,  # Unlimited results
                    search_all=False
                )
            else:
                result = await tool(
                    pattern=pattern,
                    path=test_drive,
                    max_results=0,  # Unlimited results
                    search_all=False
                )
            
            duration = time.time() - start
            
            if result.get("success"):
                count = result.get("count", 0)
                files_per_sec = count / duration if duration > 0 else 0
                
                # Format large numbers
                count_str = f"{count:,}" if count >= 1000 else str(count)
                duration_str = f"{duration:.2f}s" if duration >= 1 else f"{duration*1000:.0f}ms"
                
                print(f"      Found: {count_str} files in {duration_str}")
                print(f"      Speed: {files_per_sec:,.0f} files/sec")
                
                all_results.append({
                    "pattern": pattern,
                    "count": count,
                    "duration": duration,
                    "files_per_sec": files_per_sec,
                    "success": True
                })
            else:
                error_msg = result.get("error", "Unknown error")
                print(f"      FAILED: {error_msg}")
                all_results.append({
                    "pattern": pattern,
                    "success": False,
                    "error": error_msg
                })
                
        except Exception as e:
            duration = time.time() - start
            print(f"      EXCEPTION: {str(e)}")
            all_results.append({
                "pattern": pattern,
                "success": False,
                "error": str(e),
                "duration": duration
            })
    
    # Summary
    successful_tests = [r for r in all_results if r.get("success")]
    failed_tests = [r for r in all_results if not r.get("success")]
    
    if successful_tests:
        total_files = sum(r["count"] for r in successful_tests)
        total_duration = sum(r["duration"] for r in successful_tests)
        avg_files_per_sec = sum(r["files_per_sec"] for r in successful_tests) / len(successful_tests)
        
        details = (
            f"Total: {total_files:,} files in {total_duration:.1f}s | "
            f"Avg: {avg_files_per_sec:,.0f} files/sec | "
            f"Patterns: {len(successful_tests)}/{len(test_patterns)}"
        )
        
        if failed_tests:
            details += f" | {len(failed_tests)} failed"
        
        results.add_pass(test_name, total_duration, details)
        return True
    else:
        error_details = "; ".join(f"{r['pattern']}: {r.get('error', 'Unknown')}" for r in failed_tests)
        results.add_fail(test_name, f"All tests failed: {error_details}", 0)
        return False


async def test_drive_inventory():
    """Test drive inventory tool."""
    test_name = "Drive Inventory"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = drive_inventory
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)()
        else:
            result = await tool()
        duration = time.time() - start
        if result.get("success"):
            drives = result.get("drives", [])
            results.add_pass(
                test_name,
                duration,
                f"Found {len(drives)} NTFS drives",
            )
            return True
        else:
            results.add_fail(
                test_name,
                f"Failed: {result.get('error', 'Unknown')}",
                duration,
            )
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_service_status():
    """Test service status tool."""
    test_name = "Service Status"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = service_status
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)()
        else:
            result = await tool()
        duration = time.time() - start
        if result.get("running") is not None:
            status = "running" if result.get("running") else "stopped"
            results.add_pass(test_name, duration, f"Service is {status}")
            return True
        else:
            results.add_fail(test_name, "Invalid response", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_help_tool():
    """Test help tool."""
    test_name = "Help Tool"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = help
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(level="basic")
        else:
            result = await tool(level="basic")
        duration = time.time() - start
        if result.get("count", 0) > 0:
            count = result.get("count", 0)
            results.add_pass(test_name, duration, f"Found {count} tools")
            return True
        else:
            results.add_fail(test_name, "No tools found", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_help_intermediate():
    """Test help tool at intermediate level."""
    test_name = "Help Tool - Intermediate"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = help
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(level="intermediate")
        else:
            result = await tool(level="intermediate")
        duration = time.time() - start
        if result.get("count", 0) > 0:
            count = result.get("count", 0)
            results.add_pass(test_name, duration, f"Found {count} tools")
            return True
        else:
            results.add_fail(test_name, "No tools found", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_ntfs_volume_info():
    """Test NTFS volume info."""
    test_name = "NTFS Volume Info"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = ntfs_volume_info
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)("C:\\")
        else:
            result = await tool("C:\\")
        duration = time.time() - start
        if result.get("volume_path"):
            results.add_pass(test_name, duration, "Volume info retrieved")
            return True
        else:
            results.add_fail(test_name, "Invalid response", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_ntfs_list_volumes():
    """Test NTFS list volumes."""
    test_name = "NTFS List Volumes"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = ntfs_list_volumes
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)()
        else:
            result = await tool()
        duration = time.time() - start
        if isinstance(result, list) and len(result) > 0:
            results.add_pass(test_name, duration, f"Found {len(result)} volumes")
            return True
        else:
            results.add_fail(test_name, "No volumes found", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_disk_usage():
    """Test disk usage analysis."""
    test_name = "Disk Usage Analysis"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = analyze_disk_usage
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(path="C:\\", max_depth=2, find_large_files=False)
        else:
            result = await tool(path="C:\\", max_depth=2, find_large_files=False)
        duration = time.time() - start
        if result.get("status") == "completed":
            results.add_pass(test_name, duration, "Analysis completed")
            return True
        else:
            results.add_fail(test_name, f"Failed: {result.get('error', 'Unknown')}", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def test_list_services():
    """Test list services."""
    test_name = "List Services"
    print(f"\n>>> Running: {test_name}...")
    sys.stdout.flush()
    start = time.time()
    try:
        tool = list_services
        if hasattr(tool, "fn"):
            result = await (tool.fn if hasattr(tool, "fn") else tool)(status="running", include_details=True)
        else:
            result = await tool(status="running", include_details=True)
        duration = time.time() - start
        if result.get("services"):
            count = len(result.get("services", []))
            results.add_pass(test_name, duration, f"Found {count} running services")
            return True
        else:
            results.add_fail(test_name, "No services found", duration)
            return False
    except Exception as e:
        duration = time.time() - start
        results.add_fail(test_name, str(e), duration)
        return False


async def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("FASTSEARCH MCP COMPREHENSIVE TEST HARNESS")
    print("=" * 80)
    print()

    # Define all tests
    all_tests = [
        ("Service Connection", test_service_connection, True),
        ("Basic Search - *.py", test_basic_search, False),
        ("C++ File Search - *.cpp", test_cpp_search, False),
        ("D: Drive - *.py Search", test_d_py_search, False),
        ("Extension Length Test", test_extension_lengths, False),
        ("Search All Drives - *.txt", test_search_all_drives, False),
        ("Advanced Search - Size Filter (>1MB)", test_advanced_search_size_filter, False),
        ("Advanced Search - Date Filter (Last 7 Days)", test_advanced_search_date_filter, False),
        ("Advanced Search - Combined Filters", test_advanced_search_combined_filters, False),
        ("Speed Benchmark - 100 Results", test_speed_benchmark, False),
        ("Unlimited Results Performance - Millions of Files", test_unlimited_results_performance, False),
        ("Drive Inventory", test_drive_inventory, True),
        ("NTFS Volume Info", test_ntfs_volume_info, False),
        # ("NTFS List Volumes", test_ntfs_list_volumes, True),  # Tool removed from production
        ("Service Status", test_service_status, False),
        # ("List Services", test_list_services, True),  # Tool removed from production
        ("Help Tool", test_help_tool, True),
        ("Help Tool - Intermediate", test_help_intermediate, True),
        ("Disk Usage Analysis", test_disk_usage, False),
    ]

    results.set_total(len(all_tests))

    # Service connection test first
    service_available = False
    for test_name, test_func, _ in all_tests[:1]:
        service_available = await test_func()
        if not service_available:
            print("\n[WARNING] Service not available. Some tests will be skipped.\n")
            sys.stdout.flush()

    # Run remaining tests
    print("\n" + "=" * 80)
    print("RUNNING ALL TESTS")
    print("=" * 80)
    sys.stdout.flush()

    for test_name, test_func, can_run_without_service in all_tests[1:]:
        if not service_available and not can_run_without_service:
            results.add_skip(test_name, "Service not available")
            continue
        try:
            await test_func()
        except Exception as e:
            results.add_fail(test_name, f"Unexpected error: {e}", 0)

    print("\n" + "=" * 80)
    results.summary()


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        results.summary()
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        results.summary()
        sys.exit(1)
