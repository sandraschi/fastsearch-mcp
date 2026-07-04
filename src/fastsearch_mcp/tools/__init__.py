"""
FastSearch MCP Tools - FastMCP 3.2 compliant tool implementations.

This module provides all the tools available in the FastSearch MCP server,
organized according to FastMCP 3.2 patterns and conventions.

FastMCP 3.2: Tools registered via @mcp.tool decorator at import time.
Sampling: Use ctx: Context = None in tool functions for client-side LLM access.
CodeMode: Enable via --agentic flag for discovery + execute meta-tools.

PRODUCTION TOOL SET: 18 tools
See docs/TOOL_REDUCTION_PLAN.md and docs/TOOL_ENHANCEMENT_PROPOSALS.md for details.
"""

# ============================================================================
# CORE SEARCH TOOLS (3) - MUST KEEP
# ============================================================================
from .file_name_search import fastsearch_search
from .advanced_search import fastsearch_search_advanced
from .file_search import file_content_search

# ============================================================================
# FASTSEARCH SERVICE MANAGEMENT (4) - KEEP (Essential)
# ============================================================================
from .service_status import service_status
from .service import (
    service_start_fastsearch,
    service_stop_fastsearch,
    service_restart_fastsearch,
)

# ============================================================================
# ESSENTIAL UTILITIES (3) - KEEP
# ============================================================================
from .help import help
from .drive_inventory import drive_inventory
from .disk_analyzer import analyze_disk_usage
from .disk_treemap import generate_disk_treemap

# ============================================================================
# ADDITIONAL USEFUL TOOLS (5) - KEEP
# ============================================================================
from .duplicate_finder import find_duplicate_files
from .ntfs import ntfs_volume_info
from .resource_monitor import get_process_info, monitor_system_resources
from .integrity_checker import generate_file_hashes

# ============================================================================
# SEARCH RESULT ENHANCEMENT TOOLS (3) - NEW - Build on superfast search
# ============================================================================
from .search_result_analyze import search_result_analyze
from .search_result_export import search_result_export
from .search_result_filter import search_result_filter
from .llm_discovery import list_local_models

# ============================================================================
# REMOVED FROM PRODUCTION (14 tools) - Keep implementations, don't register
# ============================================================================
# Service Management - Admin Operations (3):
# - service_install_fastsearch (admin operation, rare)
# - service_uninstall_fastsearch (admin operation, rare)
# - service_repair_fastsearch (admin operation, rare)

# General Windows Service Manager (7) - Too broad, not core:
# - list_services
# - get_service
# - start_service (duplicate of FastSearch-specific)
# - stop_service (duplicate of FastSearch-specific)
# - restart_service (duplicate of FastSearch-specific)
# - set_service_startup_type (admin, not common)
# - get_service_logs (debugging, not core)

# Specialized/Nice-to-Have (4):
# - service_status_fastsearch (duplicate of service_status)
# - ntfs_check_health (specialized diagnostic)
# - ntfs_list_volumes (duplicate of drive_inventory)
# - check_file_integrity (specialized use case)

# To re-enable any tool, uncomment the import above and add to __all__

__all__ = [
    # Core Search Tools (3)
    "fastsearch_search",
    "fastsearch_search_advanced",
    "file_content_search",
    # FastSearch Service Management (4)
    "service_status",
    "service_start_fastsearch",
    "service_stop_fastsearch",
    "service_restart_fastsearch",
    # Essential Utilities (3)
    "help",
    "drive_inventory",
    "analyze_disk_usage",
    # Additional Useful Tools (5)
    "find_duplicate_files",
    "ntfs_volume_info",
    "get_process_info",
    "monitor_system_resources",
    "generate_file_hashes",
    # Search Result Enhancement Tools (3)
    "search_result_analyze",
    "search_result_export",
    "search_result_filter",
]

# Ensure tools are registered (side effect of import)
# These assignments ensure the imports execute and register tools via @mcp.tool decorator
# Ensure tools are registered (side effect of import)
# These assignments ensure the imports execute and register tools via @mcp.tool decorator
_ = fastsearch_search
_ = fastsearch_search_advanced
_ = file_content_search
_ = service_status
_ = service_start_fastsearch
_ = service_stop_fastsearch
_ = service_restart_fastsearch
_ = help
_ = drive_inventory
_ = analyze_disk_usage
_ = find_duplicate_files
_ = ntfs_volume_info
_ = get_process_info
_ = monitor_system_resources
_ = generate_file_hashes
_ = search_result_analyze
_ = search_result_export
_ = search_result_filter

# Unregister tools that were imported but shouldn't be in production
# (Importing modules registers ALL tools in those modules, so we need to unregister unwanted ones)
from ..mcp_instance import mcp
import logging

# Tools to remove from production
_TOOLS_TO_REMOVE = {
    # Service Management - Admin Operations (3)
    "service_install_fastsearch",
    "service_uninstall_fastsearch",
    "service_repair_fastsearch",
    # General Windows Service Manager (7)
    "list_services",
    "get_service",
    "start_service",
    "stop_service",
    "restart_service",
    "set_service_startup_type",
    "get_service_logs",
    # Specialized/Nice-to-Have (4)
    "service_status_fastsearch",  # Duplicate of service_status
    "ntfs_check_health",
    "ntfs_list_volumes",
    "check_file_integrity",
}

# FastMCP 3.x: use disable() instead of remove_tool(); targets by name
_logger = logging.getLogger(__name__)
try:
    mcp.disable(names=_TOOLS_TO_REMOVE, components={"tool"})
except LookupError as e:
    _logger.warning("Tool disable failed (some names may not exist): %s", e)
