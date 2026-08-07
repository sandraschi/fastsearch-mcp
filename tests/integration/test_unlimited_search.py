#!/usr/bin/env python3
"""
Run just the unlimited search performance test.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.pipe_client import search_files_via_pipe


async def test_unlimited_search():
    """Test unlimited search performance."""
    print("=" * 70)
    print("UNLIMITED SEARCH PERFORMANCE TEST")
    print("=" * 70)
    print()

    # Test patterns that typically match many files
    test_patterns = [
        ("*.dll", "DLL files (system files)"),
        ("*.exe", "Executable files"),
        ("*.txt", "Text files"),
    ]

    # Test on C: drive
    test_drive = "C:\\"

    all_results = []

    for pattern, description in test_patterns:
        print(f"\n🔍 Testing: {pattern} ({description})")
        print(f"   Path: {test_drive}")
        print("   Max results: Unlimited (0)")
        sys.stdout.flush()

        start = time.time()
        try:
            results = await search_files_via_pipe(
                pattern=pattern,
                directory=test_drive,
                max_results=0,  # Unlimited results
                timeout=600,  # 10 minute timeout for large searches
            )

            # Convert results to expected format
            result = {"success": True, "count": len(results) if results else 0, "results": results or []}

            duration = time.time() - start

            if result.get("success"):
                count = result.get("count", 0)
                files_per_sec = count / duration if duration > 0 else 0

                # Format large numbers
                count_str = f"{count:,}" if count >= 1000 else str(count)
                duration_str = f"{duration:.2f}s" if duration >= 1 else f"{duration * 1000:.0f}ms"

                print(f"   ✅ Found: {count_str} files in {duration_str}")
                print(f"   ⚡ Speed: {files_per_sec:,.0f} files/sec")

                all_results.append(
                    {
                        "pattern": pattern,
                        "count": count,
                        "duration": duration,
                        "files_per_sec": files_per_sec,
                        "success": True,
                    }
                )
            else:
                error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
                print(f"   ❌ FAILED: {error_msg}")
                all_results.append({"pattern": pattern, "success": False, "error": error_msg})

        except Exception as e:
            duration = time.time() - start
            error_msg = str(e)
            print(f"   ❌ EXCEPTION: {error_msg}")
            import traceback

            traceback.print_exc()
            all_results.append({"pattern": pattern, "success": False, "error": error_msg, "duration": duration})

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    successful_tests = [r for r in all_results if r.get("success")]
    failed_tests = [r for r in all_results if not r.get("success")]

    if successful_tests:
        total_files = sum(r["count"] for r in successful_tests)
        total_duration = sum(r["duration"] for r in successful_tests)
        avg_files_per_sec = sum(r["files_per_sec"] for r in successful_tests) / len(successful_tests)

        print(f"\n✅ Successful: {len(successful_tests)}/{len(test_patterns)} patterns")
        print(f"   Total files found: {total_files:,}")
        print(f"   Total time: {total_duration:.2f}s")
        print(f"   Average speed: {avg_files_per_sec:,.0f} files/sec")

        print("\n📊 Per-pattern results:")
        for r in successful_tests:
            print(
                f"   {r['pattern']}: {r['count']:,} files in {r['duration']:.2f}s ({r['files_per_sec']:,.0f} files/sec)"
            )

    if failed_tests:
        print(f"\n❌ Failed: {len(failed_tests)}/{len(test_patterns)} patterns")
        for r in failed_tests:
            print(f"   {r['pattern']}: {r.get('error', 'Unknown error')}")

    print()


if __name__ == "__main__":
    asyncio.run(test_unlimited_search())
