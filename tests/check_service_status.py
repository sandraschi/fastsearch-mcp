#!/usr/bin/env python3
"""Check FastSearch service status."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.tools.service import service_status_fastsearch


async def main():
    result = await (
        service_status_fastsearch.fn if hasattr(service_status_fastsearch, "fn") else service_status_fastsearch
    )()
    print(f"Status: {result.get('status')}")
    print(f"Full result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
