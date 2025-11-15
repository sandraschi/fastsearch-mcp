#!/usr/bin/env python3
"""
FastSearch MCP Server - Main entry point.

This module provides the main entry point for the FastSearch MCP server,
following FastMCP 2.13 patterns and conventions.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from fastsearch_mcp import FastSearchServer, __version__  # noqa: E402


def print_banner() -> None:
    """Print the FastSearch MCP server banner."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    FastSearch MCP Server                   ║
║                      Version {__version__}                      ║
║                                                              ║
║  🚀 Direct NTFS MFT Access • Real-time Search              ║
║  ⚡ Sub-100ms Performance • <50MB Memory                    ║
║  🎯 Instant Startup • FastMCP 2.13 Compliant              ║
╚══════════════════════════════════════════════════════════════╝
""")


async def main() -> None:
    """Main async entry point."""
    print_banner()

    try:
        # Create and run the server
        server = FastSearchServer()
        await server.start()

    except KeyboardInterrupt:
        # Server was interrupted - this is normal
        pass
    except Exception as e:
        print(f"❌ Server error: {e}", file=sys.stderr)
        raise


def cli_main() -> None:
    """CLI entry point."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Don't print to stdout after interruption - it may be closed
        pass
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
