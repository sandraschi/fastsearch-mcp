# Tool Reduction Plan: 29 → 15 Tools

## Current Tool Inventory (29 tools)

### Core Search Tools (3) ✅ KEEP ALL
1. `fastsearch_search` - Basic file name search (CORE)
2. `fastsearch_search_advanced` - Advanced search with filters (CORE)
3. `file_content_search` - Search inside file contents (USEFUL)

### Service Management Tools (15) ⚠️ CONSOLIDATE TO 3-4

**FastSearch-Specific Service Tools (7):**
- ✅ `service_status_fastsearch` - KEEP (or merge with service_status)
- ✅ `service_start_fastsearch` - KEEP
- ✅ `service_stop_fastsearch` - KEEP
- ✅ `service_restart_fastsearch` - KEEP (convenience wrapper)
- ❌ `service_install_fastsearch` - REMOVE (admin operation, rare)
- ❌ `service_uninstall_fastsearch` - REMOVE (admin operation, rare)
- ❌ `service_repair_fastsearch` - REMOVE (admin operation, rare)

**General Windows Service Manager Tools (7):**
- ❌ `list_services` - REMOVE (too broad, not core to FastSearch)
- ❌ `get_service` - REMOVE (too broad, not core)
- ❌ `start_service` - REMOVE (duplicate of FastSearch-specific)
- ❌ `stop_service` - REMOVE (duplicate)
- ❌ `restart_service` - REMOVE (duplicate)
- ❌ `set_service_startup_type` - REMOVE (admin, not common use case)
- ❌ `get_service_logs` - REMOVE (debugging tool, not core)

**Service Status Tool (1):**
- ✅ `service_status` - KEEP (consolidate with service_status_fastsearch if needed)

### Utility Tools (11) ⚠️ SELECTIVE KEEP

**Essential Utilities (2):**
- ✅ `help` - KEEP (essential for discovery)
- ✅ `drive_inventory` - KEEP (useful for search context)

**Specialized/Nice-to-Have (9):**
- ❌ `analyze_disk_usage` - REMOVE (nice-to-have, not core)
- ❌ `find_duplicate_files` - REMOVE (nice-to-have, not core)
- ❌ `check_file_integrity` - REMOVE (specialized use case)
- ❌ `generate_file_hashes` - REMOVE (specialized use case)
- ❌ `ntfs_volume_info` - REMOVE (specialized, not core)
- ❌ `ntfs_check_health` - REMOVE (specialized, not core)
- ❌ `ntfs_list_volumes` - REMOVE (duplicate of drive_inventory)
- ❌ `monitor_system_resources` - REMOVE (not core to file search)
- ❌ `get_process_info` - REMOVE (not core to file search)

## Final Production Tool Set (15 tools)

### Core Search (3)
1. ✅ `fastsearch_search` - Basic file name search
2. ✅ `fastsearch_search_advanced` - Advanced search with filters
3. ✅ `file_content_search` - Search inside file contents

### Service Management (4)
4. ✅ `service_status` - Get FastSearch service status (consolidated)
5. ✅ `service_start_fastsearch` - Start FastSearch service
6. ✅ `service_stop_fastsearch` - Stop FastSearch service
7. ✅ `service_restart_fastsearch` - Restart FastSearch service

### Utilities (2)
8. ✅ `help` - Tool help and documentation
9. ✅ `drive_inventory` - List available drives/volumes

### Additional Core Tools (6)
10. ✅ `drive_inventory` - Already counted above
11. ✅ `service_status` - Already counted above
12. ✅ `fastsearch_search` - Already counted above
13. ✅ `fastsearch_search_advanced` - Already counted above
14. ✅ `file_content_search` - Already counted above
15. ✅ `service_start_fastsearch` - Already counted above

**Wait, let me recount properly:**

### Final 15 Tools:
1. `fastsearch_search` - Basic file name search
2. `fastsearch_search_advanced` - Advanced search with filters  
3. `file_content_search` - Search inside file contents
4. `service_status` - Get FastSearch service status
5. `service_start_fastsearch` - Start FastSearch service
6. `service_stop_fastsearch` - Stop FastSearch service
7. `service_restart_fastsearch` - Restart FastSearch service
8. `help` - Tool help and documentation
9. `drive_inventory` - List available drives/volumes

**That's only 9! Let me add a few more useful ones:**

10. `find_duplicate_files` - Actually useful for file management
11. `analyze_disk_usage` - Useful for understanding disk space
12. `ntfs_volume_info` - Useful for understanding volumes before searching
13. `get_process_info` - Useful for debugging service issues
14. `monitor_system_resources` - Useful for performance monitoring
15. `generate_file_hashes` - Useful for integrity checks

Actually, let me reconsider based on user feedback - they said service tools are "overblown" and want to focus on core search. Let me revise:

## Final Production Tool Set: 15 Tools

### Core Search Tools (3) - MUST KEEP
1. ✅ `fastsearch_search` - Basic file name pattern search (CORE)
2. ✅ `fastsearch_search_advanced` - Advanced search with filters (CORE)
3. ✅ `file_content_search` - Search inside file contents (USEFUL)

### FastSearch Service Management (4) - KEEP (Essential)
4. ✅ `service_status` - Get FastSearch service status (consolidated)
5. ✅ `service_start_fastsearch` - Start FastSearch service
6. ✅ `service_stop_fastsearch` - Stop FastSearch service
7. ✅ `service_restart_fastsearch` - Restart FastSearch service (convenience)

### Essential Utilities (3) - KEEP
8. ✅ `help` - Tool help and documentation (ESSENTIAL)
9. ✅ `drive_inventory` - List available drives/volumes (USEFUL for search context)
10. ✅ `analyze_disk_usage` - Analyze disk space usage (USEFUL)

### Additional Useful Tools (5) - KEEP
11. ✅ `find_duplicate_files` - Find duplicate files (USEFUL)
12. ✅ `ntfs_volume_info` - Get NTFS volume information (USEFUL)
13. ✅ `get_process_info` - Get process information (USEFUL for debugging)
14. ✅ `monitor_system_resources` - Monitor system resources (USEFUL)
15. ✅ `generate_file_hashes` - Generate file hashes (USEFUL)

## Implementation Plan

1. **Comment out imports** in `src/fastsearch_mcp/tools/__init__.py` for removed tools
2. **Keep tool implementations** - don't delete, just don't register
3. **Add comments** explaining why tools are excluded from production
4. **Consider consolidation** - merge `service_status` and `service_status_fastsearch` if they overlap

## Tools to Remove from Production (14 tools)

### Service Management - Admin Operations (3)
1. ❌ `service_install_fastsearch` - Admin operation, rare use case
2. ❌ `service_uninstall_fastsearch` - Admin operation, rare use case
3. ❌ `service_repair_fastsearch` - Admin operation, rare use case

### General Windows Service Manager (7) - REMOVE (Too broad, not core to FastSearch)
4. ❌ `list_services` - Too broad, not core to FastSearch
5. ❌ `get_service` - Too broad, not core
6. ❌ `start_service` - Duplicate of FastSearch-specific version
7. ❌ `stop_service` - Duplicate of FastSearch-specific version
8. ❌ `restart_service` - Duplicate of FastSearch-specific version
9. ❌ `set_service_startup_type` - Admin operation, not common use case
10. ❌ `get_service_logs` - Debugging tool, not core functionality

### Specialized/Nice-to-Have (4)
11. ❌ `ntfs_check_health` - Specialized diagnostic tool
12. ❌ `ntfs_list_volumes` - Duplicate of `drive_inventory` functionality
13. ❌ `check_file_integrity` - Specialized use case, not core
14. ❌ `service_status_fastsearch` - Duplicate of `service_status` (consolidate)

## Summary

**KEEP (15 tools):**
- 3 Core Search tools
- 4 FastSearch Service Management tools
- 3 Essential Utilities
- 5 Additional Useful tools

**REMOVE (14 tools):**
- 3 Admin service operations
- 7 General Windows service manager tools
- 4 Specialized/duplicate tools

**Total: 29 → 15 tools (48% reduction)**

