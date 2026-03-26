#!/usr/bin/env python3
"""Check FastSearch service status with detailed info."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.tools.service_manager import get_service


async def main():
    try:
        result = await (get_service.fn if hasattr(get_service, "fn") else get_service)("FastSearchService")
        print(f"Service found: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

