"""
Test service with UAC elevation and read Windows Event Logs.

This script will:
1. Check for admin privileges (prompt for elevation if needed)
2. Start the service
3. Read Windows Event Logs to see what happened
4. Test pipe connection
5. Stop the service
"""

import asyncio
import ctypes
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.pipe_client import get_service_info_via_pipe, test_pipe_connection
from fastsearch_mcp.service_client import (
    SERVICE_NAME,
    get_service_status,
    is_service_running,
    start_service,
    stop_service,
)


def is_admin():
    """Check if running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False


def read_service_event_logs(service_name: str = "FastSearchMCP", minutes: int = 10):
    """Read Windows Event Logs for the service."""
    try:
        import win32con
        import win32evtlog
        import win32evtlogutil

        print(f"\n{'=' * 60}")
        print(f"Reading Event Logs for {service_name} (last {minutes} minutes)")
        print(f"{'=' * 60}")

        # Open Application log
        hand = win32evtlog.OpenEventLog(None, "Application")
        if not hand:
            print("ERROR: Could not open Application event log")
            return []

        try:
            # Read events backwards (newest first)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

            # Calculate time threshold
            cutoff_time = datetime.now() - timedelta(minutes=minutes)

            events = []
            count = 0
            max_events = 100

            while count < max_events:
                try:
                    event_logs = win32evtlog.ReadEventLog(hand, flags, 0)
                    if not event_logs:
                        break

                    for event in event_logs:
                        # Check if event is from our service
                        source = event.SourceName if hasattr(event, "SourceName") else ""
                        if service_name.lower() not in source.lower():
                            continue

                        # Check time
                        event_time = event.TimeGenerated
                        if event_time < cutoff_time:
                            continue

                        # Get event type
                        event_type_map = {
                            win32con.EVENTLOG_ERROR_TYPE: "ERROR",
                            win32con.EVENTLOG_WARNING_TYPE: "WARNING",
                            win32con.EVENTLOG_INFORMATION_TYPE: "INFO",
                            win32con.EVENTLOG_AUDIT_SUCCESS: "AUDIT_SUCCESS",
                            win32con.EVENTLOG_AUDIT_FAILURE: "AUDIT_FAILURE",
                        }
                        event_type = event_type_map.get(event.EventType, "UNKNOWN")

                        # Get message
                        try:
                            message = win32evtlogutil.SafeFormatMessage(event, "Application")
                        except Exception:
                            message = "Could not format message"

                        events.append(
                            {
                                "time": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "type": event_type,
                                "source": source,
                                "event_id": event.EventID,
                                "message": message,
                            }
                        )
                        count += 1

                except Exception as e:
                    if "no more items" in str(e).lower():
                        break
                    print(f"Error reading events: {e}")
                    break

            return events

        finally:
            win32evtlog.CloseEventLog(hand)

    except ImportError:
        print("ERROR: win32evtlog not available. Install pywin32.")
        return []
    except Exception as e:
        print(f"ERROR reading event logs: {e}")
        return []


async def test_service_with_logs():
    """Test service operations and read logs."""
    print("=" * 60)
    print("FastSearch Service Test with Event Log Reading")
    print("=" * 60)

    # Check admin privileges
    admin = is_admin()
    print(f"\n1. Admin Privileges: {'YES [OK]' if admin else 'NO [REQUIRED]'}")

    if not admin:
        print("\n[!] This script requires administrator privileges.")
        print("[!] Please run as administrator to test service start/stop.")
        print("[!] Reading logs without admin (may have limited access)...")

    # Read existing logs before starting
    print("\n2. Reading Event Logs (BEFORE service start):")
    logs_before = read_service_event_logs(SERVICE_NAME, minutes=5)
    if logs_before:
        print(f"   Found {len(logs_before)} recent log entries:")
        for log in logs_before[:5]:  # Show last 5
            print(f"   [{log['time']}] {log['type']}: {log['message'][:100]}")
    else:
        print("   No recent log entries found")

    # Check current status
    print("\n3. Current Service Status:")
    running = is_service_running()
    print(f"   Service running: {running}")

    status = await get_service_status()
    print(f"   Service state: {status.get('service_state', 'Unknown')}")
    print(f"   Executable exists: {Path(status.get('executable_path', '')).exists()}")

    # Try to start service if admin
    if admin:
        print("\n4. Starting Service:")
        if running:
            print("   Service already running, stopping first...")
            await stop_service()
            await asyncio.sleep(2)

        print("   Attempting to start service...")
        start_result = await start_service()
        print(f"   Start result: {start_result}")

        # Wait a bit for service to start (or crash)
        await asyncio.sleep(5)

        # Check if running
        running_after = is_service_running()
        print(f"   Service running after start: {running_after}")

        # Read logs after start attempt
        print("\n5. Reading Event Logs (AFTER service start attempt):")
        logs_after = read_service_event_logs(SERVICE_NAME, minutes=2)
        if logs_after:
            print(f"   Found {len(logs_after)} recent log entries:")
            for log in logs_after:
                print(f"   [{log['time']}] {log['type']} (ID: {log['event_id']}):")
                print(f"      {log['message']}")
        else:
            print("   No new log entries found")

        # Test pipe connection if running
        if running_after:
            print("\n6. Testing Pipe Connection:")
            pipe_connected = await test_pipe_connection()
            print(f"   Pipe connection: {'SUCCESS [OK]' if pipe_connected else 'FAILED [ERROR]'}")

            if pipe_connected:
                try:
                    info = await get_service_info_via_pipe()
                    if info:
                        print(f"   Service info: {info}")
                except Exception as e:
                    print(f"   Service info error: {e}")

        # Try to stop
        print("\n7. Stopping Service:")
        stop_result = await stop_service()
        print(f"   Stop result: {stop_result}")
        await asyncio.sleep(2)

        # Read logs after stop
        print("\n8. Reading Event Logs (AFTER service stop):")
        logs_final = read_service_event_logs(SERVICE_NAME, minutes=1)
        if logs_final:
            print(f"   Found {len(logs_final)} recent log entries:")
            for log in logs_final:
                print(f"   [{log['time']}] {log['type']}: {log['message'][:100]}")
    else:
        print("\n4-8. Service Control: SKIPPED (requires admin privileges)")
        print("   To test start/stop, run this script as administrator")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_service_with_logs())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback

        traceback.print_exc()
