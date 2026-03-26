#!/usr/bin/env python3
"""
Test pagination functionality with FastSearch MCP.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.tools import fastsearch_search


async def test_pagination():
    """Test pagination with different scenarios."""
    print("=" * 70)
    print("PAGINATION TEST")
    print("=" * 70)
    print()
    
    # Test 1: Basic search without pagination (default behavior)
    print("Test 1: Basic search (no pagination)")
    print("-" * 70)
    try:
        result = await fastsearch_search(
            pattern="*.py",
            path="C:\\",
            max_results=100,
            pagination_mode="none"
        )
        print(f"✅ Success: Found {result.get('count', 0)} results")
        print(f"   Pagination: {result.get('pagination')}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print()
    
    # Test 2: Paginated search - Page 1
    print("Test 2: Paginated search - Page 1")
    print("-" * 70)
    try:
        result = await fastsearch_search(
            pattern="*.py",
            path="C:\\",
            max_results=0,  # Unlimited (capped at 10M)
            pagination_mode="offset",
            page=1,
            page_size=100
        )
        print(f"✅ Success: Found {result.get('count', 0)} results on page 1")
        pagination = result.get('pagination')
        if pagination:
            print(f"   Total results: {pagination.get('total_results', 0)}")
            print(f"   Total pages: {pagination.get('total_pages', 0)}")
            print(f"   Has next: {pagination.get('has_next', False)}")
            print(f"   Has previous: {pagination.get('has_previous', False)}")
        else:
            print("   ⚠️  No pagination metadata returned")
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Paginated search - Page 2
    print("Test 3: Paginated search - Page 2")
    print("-" * 70)
    try:
        result = await fastsearch_search(
            pattern="*.py",
            path="C:\\",
            max_results=0,
            pagination_mode="offset",
            page=2,
            page_size=100
        )
        print(f"✅ Success: Found {result.get('count', 0)} results on page 2")
        pagination = result.get('pagination')
        if pagination:
            print(f"   Page: {pagination.get('page', 0)}")
            print(f"   Total results: {pagination.get('total_results', 0)}")
            print(f"   Has next: {pagination.get('has_next', False)}")
            print(f"   Has previous: {pagination.get('has_previous', False)}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print()
    
    # Test 4: Unlimited search with pagination (dangerous pattern)
    print("Test 4: Unlimited search with pagination (*.dll)")
    print("-" * 70)
    print("⚠️  This tests pagination with a pattern that matches many files")
    try:
        result = await fastsearch_search(
            pattern="*.dll",
            path="C:\\",
            max_results=0,  # Unlimited
            pagination_mode="offset",
            page=1,
            page_size=1000
        )
        print(f"✅ Success: Found {result.get('count', 0)} results on page 1")
        pagination = result.get('pagination')
        if pagination:
            print(f"   Total results: {pagination.get('total_results', 0):,}")
            print(f"   Total pages: {pagination.get('total_pages', 0):,}")
            print(f"   Page size: {pagination.get('page_size', 0):,}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_pagination())

