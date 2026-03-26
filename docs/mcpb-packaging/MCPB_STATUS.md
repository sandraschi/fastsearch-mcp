# MCPB Format Status & Limitations

**Last Updated**: November 2025  
**MCPB Version**: 1.1.1  
**Status**: Claude Desktop Only - Limited Adoption

---

## Why MCPB Failed to Gain Widespread Adoption

### 1. **Claude Desktop Exclusivity**

MCPB (Model Context Protocol Bundle) was designed specifically for Claude Desktop's extension system. While Anthropic intended it to become a universal standard, it never gained traction outside Claude Desktop:

- **No other major MCP clients adopted it**: Cursor IDE, Windsurf, Zed, and other MCP-compatible tools use standard JSON-RPC configuration
- **Vendor lock-in**: The format is tightly coupled to Claude Desktop's UI and extension system
- **Limited ecosystem**: Without broad client support, MCPB remains a niche format

### 2. **Weird Installation UX**

The "drag-and-drop into Claude Desktop settings UI" approach is unconventional:

- **Not intuitive**: Users expect traditional installers or package managers
- **No version management**: Difficult to update or uninstall cleanly
- **Manual process**: Requires users to navigate to settings, find the extensions panel, and drag files
- **No dependency resolution**: Users must manually ensure prerequisites are met

### 3. **Lack of Standard Tooling**

Unlike established formats (npm, pip, cargo), MCPB lacks:

- **Package registry**: No central repository for discovery
- **Version management**: No semantic versioning enforcement
- **Dependency resolution**: No automatic dependency handling
- **Update mechanisms**: No built-in update system
- **Uninstall process**: Removal requires manual cleanup

### 4. **Competing Standards**

The MCP ecosystem already has better alternatives:

- **Standard MCP config**: Works across all clients (Cursor, Windsurf, Zed, Claude Desktop)
- **NPX**: Universal Node.js package execution
- **Local installation**: Direct git clone + pip install (most flexible)

### 5. **Maintenance Overhead**

For developers, MCPB adds complexity:

- **Extra build step**: Requires MCPB CLI and build process
- **Manifest complexity**: Separate manifest.json with strict format requirements
- **Testing overhead**: Must test both standard MCP and MCPB packaging
- **Documentation burden**: Need to document MCPB-specific quirks

---

## What MCPB Does Well: Prompt Templates

The **one genuinely useful feature** of MCPB is its prompt template system:

### How It Works

MCPB packages can include prompt templates that Claude Desktop automatically loads:

```json
{
  "prompts": [
    {
      "name": "system",
      "description": "System prompt defining capabilities",
      "text": "prompts/system.md"
    },
    {
      "name": "user",
      "description": "User guide and examples",
      "text": "prompts/user.md"
    },
    {
      "name": "examples",
      "description": "Example interactions",
      "text": "prompts/examples.json"
    }
  ]
}
```

### Why Prompts Are Useful

1. **System context**: Provides Claude with detailed information about your MCP server's capabilities
2. **User guidance**: Helps users understand how to interact with your tools
3. **Example interactions**: Shows Claude expected usage patterns
4. **Consistent behavior**: Ensures Claude understands your server's purpose and limitations

### Current Prompt Templates

FastSearch MCP includes:

- **`prompts/system.md`**: Architecture, tools, capabilities, constraints
- **`prompts/user.md`**: User guide with examples and common use cases
- **`prompts/examples.json`**: Example interactions demonstrating tool usage

---

## Replicating Prompt Templates with Other Install Methods

**Good news**: Prompt templates can be used with any installation method!

### Option 1: Include in Documentation

The prompt templates are already in the repository at `prompts/`. Users can:

1. Read `prompts/system.md` to understand capabilities
2. Reference `prompts/user.md` for usage examples
3. Use `prompts/examples.json` as a reference

**Location**: `prompts/` directory in repository root

### Option 2: Manual Claude Desktop Configuration

For Claude Desktop users using standard MCP config (not MCPB), you can manually add prompts:

```json
{
  "mcpServers": {
    "fastsearch-mcp": {
      "command": "python",
      "args": ["-m", "fastsearch_mcp"],
      "env": {
        "PYTHONPATH": "${PWD}/src"
      },
      "prompts": {
        "system": "file:///path/to/prompts/system.md",
        "user": "file:///path/to/prompts/user.md"
      }
    }
  }
}
```

**Note**: Claude Desktop's support for prompts in standard MCP config is limited compared to MCPB.

### Option 3: Embed in Tool Descriptions

The most universal approach: Include prompt content in tool docstrings and descriptions. FastMCP automatically exposes these to all MCP clients:

```python
@mcp.tool()
async def fastsearch_search(
    pattern: str,
    path: str = "C:\\",
    max_results: int = 100
) -> Dict[str, Any]:
    """
    Search for files using direct NTFS Master File Table access.
    
    This tool provides lightning-fast file search by reading directly
    from the NTFS MFT, bypassing traditional filesystem traversal.
    
    Examples:
        - Search for Python files: pattern="*.py", path="C:\\Users"
        - Find config files: pattern="*.config", path="D:\\Projects"
    
    Architecture:
        Uses FastSearch Windows service for direct MFT access.
        Requires service to be running (check with service_status tool).
    """
```

**Advantage**: Works with ALL MCP clients, not just Claude Desktop.

---

## Recommendation

### Keep MCPB For:
- ✅ Claude Desktop users who want one-click installation
- ✅ Users who specifically request MCPB format
- ✅ Maintaining prompt template structure (useful reference)

### Prefer Other Methods For:
- ⭐ **NPX Installation** - Universal, works with all MCP clients
- ⭐ **Local Installation** - Most flexible, best for development
- ⭐ **Standard MCP Config** - Works everywhere, no vendor lock-in

### Best Practice:
1. **Primary**: Document NPX and local installation methods prominently
2. **Secondary**: Keep MCPB as optional convenience for Claude Desktop users
3. **Prompts**: Use prompt templates as documentation reference for all users
4. **Tool Docs**: Embed key prompt content in tool docstrings (universal compatibility)

---

## Current Status

- **MCPB Version**: 1.1.1 (latest)
- **Client Support**: Claude Desktop only
- **Maintenance**: Low priority (kept for Claude Desktop users)
- **Recommendation**: Use NPX or local installation for broader compatibility

---

**Bottom Line**: 

- **MCPB format**: Failed standard attempt - Claude Desktop only, limited adoption
- **Prompt templates**: Genuinely useful for providing structured usage scenarios and example interactions
- **Replication**: Docstrings can replicate *some* functionality (parameter examples, basic usage), but prompt templates provide better structured scenarios and interaction patterns
- **Recommendation**: Keep prompt templates as they provide value beyond what docstrings can offer, especially for usage scenarios and example interactions. MCPB remains optional, but the prompt templates themselves are worth maintaining.

