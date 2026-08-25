#!/usr/bin/env python3
"""
Test unlimited search safety checks with dangerous patterns like *.*
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.pipe_client import search_files_via_pipe


async def test_unlimited_safety():
    """Test unlimited search safety with dangerous patterns."""
    print("=" * 70)
    print("UNLIMITED SEARCH SAFETY TEST")
    print("=" * 70)
    print()
    print("⚠️  WARNING: This test uses dangerous patterns that match ALL files")
    print("   The service should apply safety limits to prevent memory exhaustion")
    print()

    # Dangerous patterns that match everything
    dangerous_patterns = [
        ("*.*", "Matches all files with extensions"),
        ("*", "Matches all files"),
        (".*", "Matches all files starting with dot"),
    ]

    # Test on C: drive (smaller test first)
    test_drive = "C:\\"

    print(f"Testing on: {test_drive}")
    print("Expected behavior:")
    print("  - Service should cap results at 10 million files")
    print("  - Service should log warnings about dangerous patterns")
    print("  - Service should stop at safety limit")
    print()

    for pattern, description in dangerous_patterns:
        print(f"\n🔍 Testing: {pattern} ({description})")
        print("   Max results: Unlimited (0)")
        sys.stdout.flush()

        start = time.time()
        try:
            results = await search_files_via_pipe(
                pattern=pattern,
                directory=test_drive,
                max_results=0,  # Unlimited results
                timeout=300,  # 5 minute timeout
            )

            duration = time.time() - start
            count = len(results) if results else 0

            # Format large numbers
            count_str = f"{count:,}" if count >= 1000 else str(count)
            duration_str = f"{duration:.2f}s" if duration >= 1 else f"{duration * 1000:.0f}ms"

            print(f"   ✅ Found: {count_str} files in {duration_str}")

            # Check if safety limit was applied
            if count >= 10000000:
                print("   ⚠️  SAFETY LIMIT HIT: Results capped at 10 million")
            elif count >= 1000000:
                print(f"   ⚠️  WARNING: Large result set ({count:,} files)")
            else:
                print("   [INFO] Result count is reasonable")

        except Exception as e:
            duration = time.time() - start
            print(f"   ❌ EXCEPTION: {e!s}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nCheck Windows Event Log for:")
    print("  - Warnings about dangerous patterns")
    print("  - Warnings about approaching safety limits")
    print("  - Information about unlimited search safety limits")
    print()


if __name__ == "__main__":
    asyncio.run(test_unlimited_safety())
