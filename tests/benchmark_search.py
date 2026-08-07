#!/usr/bin/env python3
"""
Benchmark FastSearch MCP against Windows Search
Tests full search (no limit) on large drives
"""

import subprocess
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import asyncio

    from fastsearch_mcp.pipe_client import search_files_via_pipe

    SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  FastSearch service client not available: {e}")
    SERVICE_AVAILABLE = False


def benchmark_fastsearch(pattern: str, drive: str, timeout: int = 600):
    """Benchmark FastSearch MCP service."""
    if not SERVICE_AVAILABLE:
        return None

    print(f"\n🔍 FastSearch MCP: Searching for '{pattern}' on {drive}:\\")
    print("   (No result limit - full scan)")

    start = time.time()
    try:
        # search_files_via_pipe is async, need to run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(
            search_files_via_pipe(
                pattern=pattern,
                directory=f"{drive}:\\",
                max_results=0,  # No limit - 0 means unlimited
                timeout=timeout,
            )
        )
        loop.close()
        elapsed = time.time() - start
        count = len(results)

        return {
            "success": True,
            "count": count,
            "elapsed": elapsed,
            "files_per_sec": count / elapsed if elapsed > 0 else 0,
        }
    except Exception as e:
        elapsed = time.time() - start
        return {"success": False, "error": str(e), "elapsed": elapsed}


def benchmark_windows_search(pattern: str, drive: str):
    """Benchmark Windows Search using PowerShell."""
    print(f"\n🔍 Windows Search: Searching for '{pattern}' on {drive}:\\")
    print("   (Using PowerShell Get-ChildItem -Recurse)")

    # Convert pattern: *.py -> *.py
    ps_pattern = pattern

    start = time.time()
    try:
        # Use PowerShell to search
        ps_cmd = f"""
        $ErrorActionPreference = 'SilentlyContinue'
        $results = Get-ChildItem -Path '{drive}:\\' -Filter '{ps_pattern}' -Recurse -File -ErrorAction SilentlyContinue
        $results.Count
        """

        result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, timeout=600)

        elapsed = time.time() - start

        if result.returncode == 0:
            try:
                count = int(result.stdout.strip())
            except ValueError:
                count = 0
        else:
            count = 0

        return {
            "success": True,
            "count": count,
            "elapsed": elapsed,
            "files_per_sec": count / elapsed if elapsed > 0 else 0,
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {"success": False, "error": "Timeout after 600 seconds", "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        return {"success": False, "error": str(e), "elapsed": elapsed}


def main():
    """Run benchmarks."""
    print("=" * 70)
    print("FastSearch MCP vs Windows Search Benchmark")
    print("=" * 70)

    # Test patterns
    patterns = ["*.py", "*.dll", "*.txt"]
    drives = ["C", "D"]

    results = []

    for drive in drives:
        # Check if drive exists
        if not Path(f"{drive}:\\").exists():
            print(f"\n⚠️  Drive {drive}:\\ not found, skipping...")
            continue

        for pattern in patterns:
            print(f"\n{'=' * 70}")
            print(f"Testing: {pattern} on {drive}:\\")
            print(f"{'=' * 70}")

            # FastSearch benchmark
            fastsearch_result = benchmark_fastsearch(pattern, drive)

            # Windows Search benchmark
            windows_result = benchmark_windows_search(pattern, drive)

            # Store results
            results.append(
                {"pattern": pattern, "drive": drive, "fastsearch": fastsearch_result, "windows": windows_result}
            )

            # Print comparison
            print(f"\n📊 Results for {pattern} on {drive}:\\")
            print("-" * 70)

            if fastsearch_result and fastsearch_result.get("success"):
                print("FastSearch MCP:")
                print(f"  Files found: {fastsearch_result['count']:,}")
                print(f"  Time: {fastsearch_result['elapsed']:.2f} seconds")
                print(f"  Speed: {fastsearch_result['files_per_sec']:.0f} files/sec")
            else:
                print("FastSearch MCP: FAILED")
                if fastsearch_result:
                    print(f"  Error: {fastsearch_result.get('error', 'Unknown')}")

            if windows_result and windows_result.get("success"):
                print("Windows Search:")
                print(f"  Files found: {windows_result['count']:,}")
                print(f"  Time: {windows_result['elapsed']:.2f} seconds")
                print(f"  Speed: {windows_result['files_per_sec']:.0f} files/sec")
            else:
                print("Windows Search: FAILED")
                if windows_result:
                    print(f"  Error: {windows_result.get('error', 'Unknown')}")

            # Speedup calculation
            if (
                fastsearch_result
                and fastsearch_result.get("success")
                and windows_result
                and windows_result.get("success")
            ):
                speedup = windows_result["elapsed"] / fastsearch_result["elapsed"]
                print(f"\n⚡ FastSearch is {speedup:.2f}x faster than Windows Search")

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")

    for result in results:
        pattern = result["pattern"]
        drive = result["drive"]
        fs = result["fastsearch"]
        ws = result["windows"]

        if fs and fs.get("success") and ws and ws.get("success"):
            speedup = ws["elapsed"] / fs["elapsed"]
            print(f"{pattern} on {drive}:\\ - {speedup:.2f}x faster")
        else:
            print(f"{pattern} on {drive}:\\ - Could not compare")


if __name__ == "__main__":
    main()
