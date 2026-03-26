# FastSearch MCP Tool Consolidation Plan

## Current State: 29 Tools

### Tool Inventory

#### **CORE SEARCH (Priority 1 - Must Work First!)**
1. `fastsearch_search` - Basic file name pattern search
2. `fastsearch_search_advanced` - Advanced search with filters (size, dates, attributes)
3. `file_content_search` - Search text content within files

#### **NTFS Tools (3 tools)**
4. `ntfs_list_volumes` - List all NTFS volumes
5. `ntfs_volume_info` - Get volume information
6. `ntfs_check_health` - Check volume health

#### **FastSearch Service Management (7 tools)**
7. `service_status_fastsearch` - Get FastSearch service status
8. `service_start_fastsearch` - Start FastSearch service
9. `service_stop_fastsearch` - Stop FastSearch service
10. `service_restart_fastsearch` - Restart FastSearch service
11. `service_install_fastsearch` - Install FastSearch service
12. `service_uninstall_fastsearch` - Uninstall FastSearch service
13. `service_repair_fastsearch` - Repair FastSearch service

#### **General Windows Service Management (8 tools)**
14. `list_services` - List all Windows services
15. `get_service` - Get service details
16. `start_service` - Start a Windows service
17. `stop_service` - Stop a Windows service
18. `restart_service` - Restart a Windows service
19. `set_service_startup_type` - Set service startup type
20. `get_service_logs` - Get service event logs
21. `service_status` - General service status (redundant?)

#### **Utility Tools (8 tools)**
22. `help` - Help/documentation tool
23. `drive_inventory` - List all drives
24. `analyze_disk_usage` - Analyze disk space usage
25. `find_duplicate_files` - Find duplicate files by hash
26. `check_file_integrity` - Check file integrity via hashes
27. `generate_file_hashes` - Generate file hashes
28. `monitor_system_resources` - Monitor system resources
29. `get_process_info` - Get process information

---

## Target: 15 Tools Maximum

### Proposed Portmanteau Tools

#### **1. `fastsearch_search` (Portmanteau) - 1 tool**
**Consolidates:**
- `fastsearch_search` (basic)
- `fastsearch_search_advanced` (advanced)
- `file_content_search` (content)

**Operation parameter:**
- `operation`: `"name"` | `"advanced"` | `"content"`

**Rationale:** All three are search operations. Single tool with operation parameter reduces tool count from 3 to 1.

---

#### **2. `fastsearch_services` (Portmanteau) - 1 tool**
**Consolidates:**
- `service_status_fastsearch`
- `service_start_fastsearch`
- `service_stop_fastsearch`
- `service_restart_fastsearch`
- `service_install_fastsearch`
- `service_uninstall_fastsearch`
- `service_repair_fastsearch`

**Operation parameter:**
- `operation`: `"status"` | `"start"` | `"stop"` | `"restart"` | `"install"` | `"uninstall"` | `"repair"`

**Rationale:** All FastSearch service operations in one tool. Reduces 7 tools to 1.

---

#### **3. `fastsearch_ntfs` (Portmanteau) - 1 tool**
**Consolidates:**
- `ntfs_list_volumes`
- `ntfs_volume_info`
- `ntfs_check_health`

**Operation parameter:**
- `operation`: `"list_volumes"` | `"volume_info"` | `"check_health"`

**Rationale:** All NTFS volume operations. Reduces 3 tools to 1.

---

#### **4. `fastsearch_utils` (Portmanteau) - 1 tool**
**Consolidates:**
- `drive_inventory`
- `analyze_disk_usage`
- `find_duplicate_files`
- `check_file_integrity`
- `generate_file_hashes`
- `monitor_system_resources`
- `get_process_info`

**Operation parameter:**
- `operation`: `"drive_inventory"` | `"disk_usage"` | `"duplicates"` | `"integrity"` | `"hashes"` | `"monitor"` | `"process_info"`

**Rationale:** General utility operations. Reduces 7 tools to 1.

---

#### **5. Keep Separate (High Value)**
- `help` - Essential for documentation
- `list_services` - General Windows service listing (useful)
- `get_service` - Get Windows service details (useful)
- `start_service` - Start Windows service (useful)
- `stop_service` - Stop Windows service (useful)
- `restart_service` - Restart Windows service (useful)
- `set_service_startup_type` - Configure service (useful)
- `get_service_logs` - Service diagnostics (useful)
- `service_status` - **REMOVE** (redundant with `get_service`)

---

## Final Tool Count: 13 Tools

1. `fastsearch_search` (portmanteau: name/advanced/content)
2. `fastsearch_services` (portmanteau: FastSearch service ops)
3. `fastsearch_ntfs` (portmanteau: NTFS volume ops)
4. `fastsearch_utils` (portmanteau: utility ops)
5. `help`
6. `list_services`
7. `get_service`
8. `start_service`
9. `stop_service`
10. `restart_service`
11. `set_service_startup_type`
12. `get_service_logs`

**Total: 12 tools** (under 15 limit)

---

## Alternative: More Aggressive Consolidation (10 tools)

If we want to go even further, we could consolidate Windows service management:

#### **`fastsearch_services` (Portmanteau) - 1 tool**
**Consolidates ALL service operations:**
- FastSearch service ops (7 tools)
- General Windows service ops (8 tools)

**Operation parameter:**
- `operation`: `"fastsearch_status"` | `"fastsearch_start"` | ... | `"list"` | `"get"` | `"start"` | `"stop"` | ...

**Final count: 5 tools**
1. `fastsearch_search`
2. `fastsearch_services` (all service ops)
3. `fastsearch_ntfs`
4. `fastsearch_utils`
5. `help`

---

## Implementation Priority

### Phase 1: **FIX SEARCH FIRST** (Current Priority)
- ✅ Get `fastsearch_search` working reliably
- ✅ Fix D: drive search issues
- ✅ Fix "search all drives" hanging
- ✅ Ensure pipe communication is stable

### Phase 2: Consolidation (After Search Works)
1. Create `fastsearch_search` portmanteau (combine 3 search tools)
2. Create `fastsearch_services` portmanteau (combine 7 FastSearch service tools)
3. Create `fastsearch_ntfs` portmanteau (combine 3 NTFS tools)
4. Create `fastsearch_utils` portmanteau (combine 7 utility tools)
5. Remove redundant `service_status` tool

### Phase 3: Optional Further Consolidation
- Consider consolidating Windows service management if needed

---

## Portmanteau Tool Pattern

All portmanteau tools will follow this pattern:

```python
@mcp.tool
async def fastsearch_search(
    operation: str,  # "name" | "advanced" | "content"
    # ... operation-specific parameters
) -> Dict[str, Any]:
    """
    Unified search tool supporting multiple search operations.
    
    Operations:
    - "name": Basic file name pattern search
    - "advanced": Advanced search with filters
    - "content": Search text content within files
    """
    if operation == "name":
        return await _search_name(...)
    elif operation == "advanced":
        return await _search_advanced(...)
    elif operation == "content":
        return await _search_content(...)
    else:
        raise ValueError(f"Unknown operation: {operation}")
```

---

## Notes

- **Search is the core value proposition** - must work perfectly before consolidation
- Portmanteau tools reduce tool count while maintaining functionality
- Operation parameter makes it clear what each tool does
- Backward compatibility: Can keep old tools as deprecated wrappers if needed
- Documentation must clearly explain all operations for each portmanteau tool


