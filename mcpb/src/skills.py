"""
FastMCP 3.2 skill definitions for FastSearch MCP.

Skills are composable workflow units registered at import time when supported.
"""

from fastsearch_mcp.mcp_instance import mcp

_skill = getattr(mcp, "skill", None)

if _skill is not None:

    @_skill()
    async def find_recently_modified_files() -> str:
        """Skill: Find files modified in the last 7 days across all drives."""
        return """
Use fastsearch_search_advanced with modified_after="7d" and search_all=True
to locate recently changed files across all NTFS drives. Combine with
file_pattern="*" to find all types, or narrow with "*.py", "*.docx", etc.
"""

    @_skill()
    async def cleanup_disk_space() -> str:
        """Skill: Identify large, old, or duplicate files for disk cleanup."""
        return """
1. Run analyze_disk_usage to find large folders
2. Run find_duplicate_files to locate redundant data
3. Run fastsearch_search_advanced with size filters (e.g., min_size=1073741824 for 1GB+)
4. Combine with accessed_before="365d" to find old large files
"""

    @_skill()
    async def forensic_file_audit() -> str:
        """Skill: Audit files for forensic or compliance review."""
        return """
1. Search for sensitive file types: fastsearch_search(pattern="*.xlsx", search_all=True)
2. Find hidden files: fastsearch_search_advanced(pattern="*", include_hidden=True, search_all=True)
3. Check for recent modifications in sensitive directories
4. Verify file integrity with generate_file_hashes
"""
