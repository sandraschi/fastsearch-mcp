"""Detailed pipe connection test with error reporting."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

import asyncio
import traceback

from fastsearch_mcp.pipe_client import NamedPipeClient


async def test():
    print("=" * 70)
    print("Detailed Pipe Connection Test")
    print("=" * 70)
    print()

    client = NamedPipeClient()

    print("1. Attempting to connect...")
    try:
        result = await client.connect()
        if result:
            print("   [OK] Connection successful")
            print(f"   Handle: {client.handle}")
            print(f"   Connected: {client.connected}")
        else:
            print("   [FAIL] Connection failed")
            return
    except Exception as e:
        print(f"   [ERROR] Exception during connect: {type(e).__name__}: {e}")
        traceback.print_exc()
        return

    print()
    print("2. Testing ping command...")
    try:
        response = await client.send_request({'command': 'ping'})
        if response:
            print(f"   [OK] Got response: {response}")
        else:
            print("   [FAIL] No response received")
            print("   This could mean:")
            print("     - Service is not reading from pipe")
            print("     - Service crashed during request handling")
            print("     - Pipe communication protocol mismatch")
    except Exception as e:
        print(f"   [ERROR] Exception during send_request: {type(e).__name__}: {e}")
        traceback.print_exc()

    print()
    print("3. Testing get_service_info command...")
    try:
        response = await client.send_request({'command': 'get_service_info'})
        if response:
            print(f"   [OK] Got response: {response}")
        else:
            print("   [FAIL] No response received")
    except Exception as e:
        print(f"   [ERROR] Exception during send_request: {type(e).__name__}: {e}")
        traceback.print_exc()

    print()
    print("4. Disconnecting...")
    try:
        await client.disconnect()
        print("   [OK] Disconnected")
    except Exception as e:
        print(f"   [ERROR] Exception during disconnect: {type(e).__name__}: {e}")

    print()
    print("=" * 70)
    print("Test Complete")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test())

