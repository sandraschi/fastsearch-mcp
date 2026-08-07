"""
Simple script to read FastSearch service logs from Windows Event Log.
Run this to see what the service is logging.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import asyncio

from fastsearch_mcp.tools.service_manager import GetServiceLogsTool


async def main():
    print("=" * 70)
    print("FastSearch Service Event Logs")
    print("=" * 70)
    print()

    tool = GetServiceLogsTool()

    # Read logs from last 24 hours
    print("Reading logs from last 24 hours...")
    print()

    result = await tool.execute(
        service_name="FastSearchMCP", log_type="Application", last="24h", limit=50, event_level="all"
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

                # Truncate long messages
                if len(message) > 200:
                    message = message[:200] + "..."

                # Color coding
                type_color = ""
                if "Error" in event_type:
                    type_color = "[ERROR]"
                elif "Warning" in event_type:
                    type_color = "[WARN]"
                else:
                    type_color = "[INFO]"

                print(f"{type_color} [{timestamp}] Event ID: {event_id}")
                print(f"  {message}")
                print()
        else:
            print("No log entries found for FastSearchMCP")
            print("(Service may not have logged anything recently)")
    else:
        error = result.get("error", "Unknown error")
        print(f"Error reading logs: {error}")
        print()
        print("Note: You may need administrator privileges to read some logs.")


if __name__ == "__main__":
    asyncio.run(main())
