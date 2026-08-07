"""Test NTFS MFT search functionality via the service."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import asyncio
import json

from fastsearch_mcp.pipe_client import NamedPipeClient


async def test_mft_search():
    """Test MFT search functionality."""
    print("=" * 70)
    print("NTFS MFT Search Test")
    print("=" * 70)
    print()

    client = NamedPipeClient()

    try:
        print("1. Connecting to service...")
        await client.connect()
        if not client.connected:
            print("   [FAIL] Could not connect to service")
            return
        print("   [OK] Connected")
        print()

        # Test 1: Simple pattern search
        print("2. Testing simple pattern search (*.txt)...")
        request = {"command": "search_files", "pattern": "*.txt", "directory": "C:\\Windows", "max_results": 10}

        response = await client.send_request(request)
        if response:
            print(f"   Response: {json.dumps(response, indent=2)}")
            if response.get("success"):
                results = response.get("results", [])
                print(f"   [OK] Found {len(results)} files")
                if results:
                    print("   Sample results:")
                    for i, result in enumerate(results[:3], 1):
                        print(f"     {i}. {result.get('path', 'N/A')}")
            else:
                print(f"   [FAIL] Search failed: {response.get('error', 'Unknown error')}")
        else:
            print("   [FAIL] No response received")
        print()

        # Test 2: Specific file search
        print("3. Testing specific file search (notepad.exe)...")
        request = {"command": "search_files", "pattern": "notepad.exe", "directory": "C:\\Windows", "max_results": 5}

        response = await client.send_request(request)
        if response:
            if response.get("success"):
                results = response.get("results", [])
                print(f"   [OK] Found {len(results)} files")
                for result in results:
                    print(f"     - {result.get('path', 'N/A')}")
            else:
                print(f"   [FAIL] Search failed: {response.get('error', 'Unknown error')}")
        else:
            print("   [FAIL] No response received")
        print()

        # Test 3: Pattern with wildcards
        print("4. Testing wildcard pattern (*.dll)...")
        request = {
            "command": "search_files",
            "pattern": "*.dll",
            "directory": "C:\\Windows\\System32",
            "max_results": 5,
        }

        response = await client.send_request(request)
        if response:
            if response.get("success"):
                results = response.get("results", [])
                print(f"   [OK] Found {len(results)} files (limited to 5)")
                for result in results:
                    print(f"     - {result.get('name', 'N/A')}")
            else:
                print(f"   [FAIL] Search failed: {response.get('error', 'Unknown error')}")
        else:
            print("   [FAIL] No response received")
        print()

        await client.disconnect()
        print("[OK] All tests completed!")

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mft_search())
