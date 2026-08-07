"""Simple service test script."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import asyncio

from fastsearch_mcp.pipe_client import NamedPipeClient


async def test():
    print("Testing FastSearch service...")
    print()

    client = NamedPipeClient()
    try:
        print("1. Connecting to pipe...")
        await client.connect()
        print("   [OK] Connected")
        print()

        print("2. Sending ping...")
        result = await client.send_request({"command": "ping"})
        print(f"   [OK] Response: {result}")
        print()

        print("3. Getting service info...")
        result = await client.send_request({"command": "get_service_info"})
        print(f"   [OK] Response: {result}")
        print()

        await client.disconnect()
        print("[OK] All tests passed!")

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
