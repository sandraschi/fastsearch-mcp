"""
Test MCP server as Claude Desktop would use it.

This simulates how Claude Desktop communicates with the MCP server via stdio.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp import FastSearchServer


async def simulate_claude_request(server: FastSearchServer, method: str, params: dict | None = None):
    """Simulate a JSON-RPC request from Claude Desktop."""

    print(f"\n{'=' * 70}")
    print("Simulating Claude Desktop Request")
    print(f"{'=' * 70}")
    print(f"Method: {method}")
    print(f"Params: {json.dumps(params, indent=2)}")
    print(f"{'=' * 70}\n")

    # FastMCP handles this internally, but we can test tool execution directly
    server.get_app()

    # For tools/call, we need to execute the tool
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Find and execute the tool
        from fastsearch_mcp.tools import AVAILABLE_TOOLS

        tool_class = None
        for tc in AVAILABLE_TOOLS:
            try:
                tool_def = tc.get_definition()
                if tool_def.name == tool_name:
                    tool_class = tc
                    break
            except Exception:
                continue

        if tool_class:
            try:
                tool_instance = tool_class()
                result = await tool_instance.execute(**arguments)

                response = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]},
                }

                print("[OK] Tool executed successfully")
                print("\nResponse:")
                print(json.dumps(response, indent=2))
                return response
            except Exception as e:
                response = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32603, "message": str(e)}}
                print(f"[ERROR] Tool execution failed: {e}")
                return response
        else:
            response = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
            }
            print(f"[ERROR] Tool not found: {tool_name}")
            return response

    return None


async def main():
    """Test MCP server with Claude Desktop-like requests."""
    print("=" * 70)
    print("  FastSearch MCP - Claude Desktop Integration Test")
    print("=" * 70)
    print()

    # Create server
    print("[INFO] Initializing server...")
    server = FastSearchServer()
    print("[OK] Server initialized")

    # Test 1: Initialize
    print("\n" + "=" * 70)
    print("Test 1: Initialize")
    print("=" * 70)
    await simulate_claude_request(
        server,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "claude-desktop", "version": "1.0.0"},
        },
    )

    # Test 2: List tools
    print("\n" + "=" * 70)
    print("Test 2: List Tools")
    print("=" * 70)
    from fastsearch_mcp.tools import AVAILABLE_TOOLS

    tools_list = []
    for tool_class in AVAILABLE_TOOLS:
        try:
            tool_def = tool_class.get_definition()
            tools_list.append({"name": tool_def.name, "description": tool_def.description})
        except Exception:
            pass

    print(f"[OK] Found {len(tools_list)} tools")
    print("\nAvailable tools:")
    for tool in tools_list[:5]:  # Show first 5
        print(f"  - {tool['name']}: {tool['description'][:60]}...")

    # Test 3: Call service_status tool
    print("\n" + "=" * 70)
    print("Test 3: Call service_status Tool")
    print("=" * 70)
    await simulate_claude_request(server, "tools/call", {"name": "service_status", "arguments": {}})

    # Test 4: Call file search (if service is available)
    print("\n" + "=" * 70)
    print("Test 4: Call file_content_search Tool")
    print("=" * 70)
    await simulate_claude_request(
        server,
        "tools/call",
        {
            "name": "file_content_search",
            "arguments": {
                "search_pattern": "test",
                "search_dir": "C:\\Windows",
                "file_pattern": "*.txt",
                "max_results": 5,
            },
        },
    )

    print("\n" + "=" * 70)
    print("[SUCCESS] All Claude Desktop simulation tests completed!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Restart Claude Desktop (if config was updated)")
    print("2. Try using tools in Claude Desktop")
    print("3. Check Claude Desktop logs for any errors")


if __name__ == "__main__":
    asyncio.run(main())
