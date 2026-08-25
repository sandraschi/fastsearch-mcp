#!/usr/bin/env python3
"""
Test script for FastSearch MCP implementation.
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.mcp_instance import mcp
from fastsearch_mcp.service_client import get_service_status, is_service_running


def test_service_client():
    """Test the service client."""
    print("=== Testing Service Client ===")

    # Test service status
    print(f"Service running: {is_service_running()}")


def test_fastmcp_server():
    """Test the FastMCP server."""
    print("\n=== Testing FastMCP Server ===")

    try:
        print(f"Server instance created: {mcp is not None}")
        print(f"Server name: {mcp.name}")
    except Exception as e:
        print(f"Error creating server: {e}")



def main():
    """Main test function."""
    logging.basicConfig(level=logging.INFO)

    print("FastSearch MCP Test Suite")
    print("=" * 50)

    test_service_client()
    test_fastmcp_server()

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
