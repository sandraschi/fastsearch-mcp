"""
Read System Event Logs for FastSearch service crashes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import asyncio

from fastsearch_mcp.tools.service_manager import GetServiceLogsTool


async def main():
    print("=" * 70)
    print("FastSearch Service - System Event Logs")
    print("=" * 70)
    print()

    tool = GetServiceLogsTool()

    # Read System log for service control manager events
    print("Reading System log for service events (last 7 days)...")
    print()

    result = await tool.execute(
        service_name="FastSearchMCP",
        log_type="System",
        last="7d",
        limit=50,
        event_level="all",
        source="",  # Don't filter by source, look for FastSearch in message
    )

    if result.get("success"):
        count = result.get("count", 0)
        logs = result.get("logs", [])

        print(f"Found {count} log entries:")
        print()

        if logs:
            for log in logs:
                timestamp = log.get("timestamp", "Unknown")
                event_type = log.get("event_type", "Unknown")
                event_id = log.get("event_id", "?")
                message = log.get("message", "")

                # Show full message for errors
                if "Error" in event_type or event_id in [7034, 7035, 7000, 7001]:
                    print(f"[{timestamp}] {event_type} (ID: {event_id})")
                    print(f"  {message}")
                    print()
                else:
                    msg_short = message[:200] + "..." if len(message) > 200 else message
                    print(f"[{timestamp}] {event_type} (ID: {event_id}): {msg_short}")
                    print()
        else:
            print("No log entries found")
            print()
            print("Trying to read all System logs with FastSearch in message...")
            print()

            # Try without source filter
            result2 = await tool.execute(
                service_name="", log_type="System", last="7d", limit=100, event_level="all", source=""
            )

            if result2.get("success"):
                all_logs = result2.get("logs", [])
                fastsearch_logs = [log for log in all_logs if "fastsearch" in log.get("message", "").lower()]

                if fastsearch_logs:
                    print(f"Found {len(fastsearch_logs)} entries mentioning FastSearch:")
                    print()
                    for log in fastsearch_logs[:20]:
                        timestamp = log.get("timestamp", "Unknown")
                        event_type = log.get("event_type", "Unknown")
                        event_id = log.get("event_id", "?")
                        message = log.get("message", "")
                        msg_short = message[:300] + "..." if len(message) > 300 else message
                        print(f"[{timestamp}] {event_type} (ID: {event_id})")
                        print(f"  {msg_short}")
                        print()
    else:
        error = result.get("error", "Unknown error")
        print(f"Error reading logs: {error}")


if __name__ == "__main__":
    asyncio.run(main())
