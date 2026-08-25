"""
Interactive test script for MCP tools.

This script allows you to test individual tools interactively.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.tools import AVAILABLE_TOOLS


async def test_tool(tool_name: str, **kwargs):
    """Test a specific tool."""
    print(f"\n{'=' * 70}")
    print(f"Testing tool: {tool_name}")
    print(f"{'=' * 70}\n")

    # Find tool
    tool_class = None
    for tc in AVAILABLE_TOOLS:
        try:
            tool_def = tc.get_definition()
            if tool_def.name == tool_name:
                tool_class = tc
                break
        except Exception:
            continue

    if not tool_class:
        print(f"[ERROR] Tool '{tool_name}' not found")
        print("\nAvailable tools:")
        for tc in AVAILABLE_TOOLS:
            try:
                tool_def = tc.get_definition()
                print(f"  - {tool_def.name}")
            except Exception:
                pass
        return

    # Execute tool
    try:
        tool_instance = tool_class()
        print(f"Executing {tool_name} with args: {kwargs}")
        result = await tool_instance.execute(**kwargs)

        print("\n[OK] Success!")
        print("\nResult:")
        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback

        traceback.print_exc()


async def interactive_mode():
    """Interactive tool testing."""
    print("FastSearch MCP Tools - Interactive Tester")
    print("=" * 70)
    print("\nAvailable tools:")

    tools = []
    for i, tool_class in enumerate(AVAILABLE_TOOLS, 1):
        try:
            tool_def = tool_class.get_definition()
            tools.append(tool_def.name)
            print(f"  {i}. {tool_def.name}")
        except Exception:
            pass

    print("\nEnter tool name or number (or 'q' to quit):")

    while True:
        try:
            choice = input("\n> ").strip()

            if choice.lower() == "q":
                break

            # Try number first
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(tools):
                    tool_name = tools[idx]
                else:
                    print("Invalid number")
                    continue
            except ValueError:
                tool_name = choice

            # Test the tool
            await test_tool(tool_name)

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Command line mode
        tool_name = sys.argv[1]
        args = {}

        # Parse additional args
        for arg in sys.argv[2:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                args[key] = value

        await test_tool(tool_name, **args)
    else:
        # Interactive mode
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
