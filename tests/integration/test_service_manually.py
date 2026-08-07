"""
Manual service test script - Run with admin privileges to test service start/stop.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import ctypes

from fastsearch_mcp.pipe_client import get_service_info_via_pipe, test_pipe_connection
from fastsearch_mcp.service_client import (
    get_service_status,
    is_service_running,
    start_service,
    stop_service,
    test_service_connection,
)


def is_admin():
    """Check if running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False


async def test_service_operations():
    """Test all service operations."""
    print("=" * 60)
    print("FastSearch Service Test")
    print("=" * 60)

    # Check admin privileges
    admin = is_admin()
    print(f"\n1. Admin Privileges: {'YES [OK]' if admin else 'NO [REQUIRED for start/stop]'}")

    # Check current status
    print("\n2. Current Service Status:")
    running = is_service_running()
    print(f"   Service running: {running}")

    status = await get_service_status()
    print(f"   Service state: {status.get('service_state', 'Unknown')}")
    print(f"   Executable exists: {Path(status.get('executable_path', '')).exists()}")
    print(f"   Pipe name: {status.get('pipe_name', 'N/A')}")

    # Test connection
    print("\n3. Connection Test:")
    conn_test = await test_service_connection()
    print(f"   Service running: {conn_test.get('service_running', False)}")
    print(f"   Pipe connected: {conn_test.get('pipe_connected', False)}")
    print(f"   Executable exists: {conn_test.get('executable_exists', False)}")

    # Test pipe connection
    print("\n4. Pipe Connection Test:")
    if running:
        pipe_connected = await test_pipe_connection()
        print(f"   Pipe connection: {'SUCCESS [OK]' if pipe_connected else 'FAILED [ERROR]'}")

        if pipe_connected:
            print("\n5. Testing Pipe Communication:")
            try:
                info = await get_service_info_via_pipe()
                if info:
                    print("   Service info retrieved: [OK]")
                    print(f"   Info: {info}")
                else:
                    print("   Service info: None (service may not be fully ready)")
            except Exception as e:
                print(f"   Service info error: {e}")
    else:
        print("   Service not running - skipping pipe tests")

    # Test start/stop if admin
    if admin:
        print("\n6. Service Control Tests:")

        # Try to start
        print("   Attempting to start service...")
        start_result = await start_service()
        if start_result:
            print("   Start: SUCCESS [OK]")
            await asyncio.sleep(3)  # Wait for service to start

            # Check if running
            running_after_start = is_service_running()
            print(f"   Service running after start: {running_after_start}")

            if running_after_start:
                # Test pipe connection
                pipe_connected = await test_pipe_connection()
                print(f"   Pipe connection after start: {'SUCCESS [OK]' if pipe_connected else 'FAILED [ERROR]'}")

                # Try to stop
                print("\n   Attempting to stop service...")
                stop_result = await stop_service()
                if stop_result:
                    print("   Stop: SUCCESS [OK]")
                    await asyncio.sleep(2)
                    running_after_stop = is_service_running()
                    print(f"   Service running after stop: {running_after_stop}")
                else:
                    print("   Stop: FAILED [ERROR]")
            else:
                print("   Service did not start successfully")
        else:
            print("   Start: FAILED [ERROR] (service may already be running or error occurred)")
    else:
        print("\n6. Service Control: SKIPPED (requires admin privileges)")
        print("   To test start/stop, run this script as administrator")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_service_operations())
