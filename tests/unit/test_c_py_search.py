"""Quick test to search for .py files on C: drive."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the module and access the function
import fastsearch_mcp.tools.file_name_search as file_name_search_module

# FastMCP wraps tools in FunctionTool objects - get the underlying function
# Based on help.py pattern: use .fn attribute
tool_wrapper = file_name_search_module.fastsearch_search

if hasattr(tool_wrapper, "fn"):
    # FastMCP FunctionTool - get the actual function
    fastsearch_search = tool_wrapper.fn
elif hasattr(tool_wrapper, "__wrapped__"):
    # Standard wrapped function
    fastsearch_search = tool_wrapper.__wrapped__
else:
    # Fallback: call the tool wrapper directly (it should be callable)
    fastsearch_search = tool_wrapper


async def main():
    print("Searching for *.md files on D: drive...")
    print("=" * 80)

    try:
        # Test with longer timeout - import search_files_via_pipe directly
        from fastsearch_mcp.service_client import search_files_via_pipe

        print("Testing with 120 second timeout...")
        results_list = await search_files_via_pipe(
            pattern="*.md",
            directory="D:\\",
            max_results=20,
            timeout=120.0  # 2 minutes
        )

        # Convert to expected format
        result = {
            "success": True,
            "pattern": "*.md",
            "path": "D:\\",
            "results": results_list,
            "count": len(results_list) if results_list else 0,
            "method": "ntfs_mft",
        }

        results = result.get("results", [])
        print(f"\nFound {len(results)} .py files on C:")
        print(f"Total matches: {result.get('total_matches', result.get('count', 'unknown'))}")
        print(f"Success: {result.get('success', 'unknown')}")
        print(f"\nResult keys: {list(result.keys())}")
        if results:
            print(f"\nFirst result structure: {list(results[0].keys())}")
            print(f"First result sample: {results[0]}")
        print("\nFirst 10 results:")
        for i, r in enumerate(results[:10], 1):
            # Results can have 'path' or 'file_path' key
            if isinstance(r, dict):
                path = r.get('path') or r.get('file_path') or r.get('name') or str(r)
            else:
                path = str(r)
            print(f"  {i}. {path}")

        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

