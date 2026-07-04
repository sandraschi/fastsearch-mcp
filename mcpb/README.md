# fastsearch-mcp (MCPB Bundle)

FastSearch MCP Server - FastMCP 3.2 NTFS search service with sampling, prompts, and CodeMode

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "fastsearch-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "fastsearch_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **health**: health
- **list_tools**: list_tools
- **call_tool**: call_tool
- **get_file**: get_file
- **llm_models**: llm_models
- **llm_chat**: llm_chat
- **llm_analyze**: llm_analyze
- **llm_analyze_forensic**: llm_analyze_forensic
- **run_tests**: run_tests
- **root_health**: root_health
- **main_stdio**: main(stdio)
- **main_http**: main(http)
- **main_sse**: main(sse)

## Requirements

- Python 3.12+
- uv
