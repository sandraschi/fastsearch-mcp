"""
Tool wrappers for FastMCP 2.13 compatibility.

This module provides individual wrapper functions for each tool to ensure
FastMCP compatibility by avoiding **kwargs signatures.
"""

from fastsearch_mcp.tools.base import _sanitize_for_json


def create_help_wrapper(tool_instance):
    """Create a wrapper for the help tool."""

    async def help_wrapper(tool_name: str = None):
        """Get help for available tools"""
        result = await tool_instance.execute(tool_name=tool_name)
        return _sanitize_for_json(result)

    return help_wrapper


def create_file_name_search_wrapper(tool_instance):
    """Create a wrapper for the simple file name search tool."""

    async def file_name_search_wrapper(
        pattern: str, path: str = "C:\\", search_all: bool = False, max_results: int = 100
    ):
        """Search for files by name pattern using direct NTFS MFT access.
        Can search all NTFS drives."""
        result = await tool_instance.execute(
            pattern=pattern, path=path, search_all=search_all, max_results=max_results
        )
        return _sanitize_for_json(result)

    return file_name_search_wrapper


def create_advanced_search_wrapper(tool_instance):
    """Create a wrapper for the advanced search tool."""

    async def advanced_search_wrapper(
        pattern: str,
        path: str = "C:\\",
        search_all: bool = False,
        max_results: int = 100,
        min_size: int = None,
        max_size: int = None,
        created_after: str = None,
        created_before: str = None,
        modified_after: str = None,
        modified_before: str = None,
        accessed_after: str = None,
        accessed_before: str = None,
        include_directories: bool = False,
        include_readonly: bool = True,
        include_hidden: bool = False,
        include_system: bool = False,
        include_compressed: bool = True,
        include_encrypted: bool = True,
    ):
        """Advanced file search using all available NTFS MFT attributes
        with comprehensive filtering."""
        result = await tool_instance.execute(
            pattern=pattern,
            path=path,
            search_all=search_all,
            max_results=max_results,
            min_size=min_size,
            max_size=max_size,
            created_after=created_after,
            created_before=created_before,
            modified_after=modified_after,
            modified_before=modified_before,
            accessed_after=accessed_after,
            accessed_before=accessed_before,
            include_directories=include_directories,
            include_readonly=include_readonly,
            include_hidden=include_hidden,
            include_system=include_system,
            include_compressed=include_compressed,
            include_encrypted=include_encrypted,
        )
        return _sanitize_for_json(result)

    return advanced_search_wrapper


def create_file_search_wrapper(tool_instance):
    """Create a wrapper for the file content search tool."""

    async def file_search_wrapper(
        search_pattern: str,
        search_dir: str,
        file_pattern: str = "*",
        exclude_dirs: list = None,
        case_sensitive: bool = False,
        whole_word: bool = False,
        max_results: int = 100,
        context_lines: int = 2,
        max_file_size_mb: int = 10,
        skip_binary: bool = True,
        min_file_size_mb: int = 0,
        modified_after: str = None,
        modified_before: str = None,
        created_after: str = None,
        created_before: str = None,
        accessed_after: str = None,
        accessed_before: str = None,
        include_hidden: bool = False,
        files_only: bool = True,
        directories_only: bool = False,
        file_attributes: list = None,
        owner: str = None,
    ):
        """Search for text patterns in files with advanced filtering"""
        result = await tool_instance.execute(
            search_pattern=search_pattern,
            search_dir=search_dir,
            file_pattern=file_pattern,
            exclude_dirs=exclude_dirs,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            max_results=max_results,
            context_lines=context_lines,
            max_file_size_mb=max_file_size_mb,
            skip_binary=skip_binary,
            min_file_size_mb=min_file_size_mb,
            modified_after=modified_after,
            modified_before=modified_before,
            created_after=created_after,
            created_before=created_before,
            accessed_after=accessed_after,
            accessed_before=accessed_before,
            include_hidden=include_hidden,
            files_only=files_only,
            directories_only=directories_only,
            file_attributes=file_attributes,
            owner=owner,
        )
        return _sanitize_for_json(result)

    return file_search_wrapper


def create_disk_analyzer_wrapper(tool_instance):
    """Create a wrapper for the disk analyzer tool."""

    async def disk_analyzer_wrapper(
        path: str = "/",
        max_depth: int = 3,
        include_partitions: bool = True,
        find_large_files: bool = True,
        large_file_limit: int = 50,
        min_file_size_mb: int = 10,
    ):
        """Analyze disk usage and find large files and directories"""
        result = await tool_instance.execute(
            path=path,
            max_depth=max_depth,
            include_partitions=include_partitions,
            find_large_files=find_large_files,
            large_file_limit=large_file_limit,
            min_file_size_mb=min_file_size_mb,
        )
        return _sanitize_for_json(result)

    return disk_analyzer_wrapper


def create_drive_inventory_wrapper(tool_instance):
    """Create a wrapper for the drive inventory tool."""

    async def drive_inventory_wrapper(filesystem_type: str = "", include_unmounted: bool = False):
        """List all connected drives and partitions with their basic information"""
        result = await tool_instance.execute(
            filesystem_type=filesystem_type, include_unmounted=include_unmounted
        )
        return _sanitize_for_json(result)

    return drive_inventory_wrapper


def create_duplicate_finder_wrapper(tool_instance):
    """Create a wrapper for the duplicate finder tool."""

    async def duplicate_finder_wrapper(
        search_dir: str,
        min_size: int = 1024,
        max_size: int = None,
        file_pattern: str = "*",
        exclude_dirs: list = None,
        fast_mode: bool = True,
        compare_content: bool = True,
        min_duplicate_group: int = 2,
        max_results: int = 100,
    ):
        """Find duplicate files based on content hashing"""
        result = await tool_instance.execute(
            search_dir=search_dir,
            min_size=min_size,
            max_size=max_size,
            file_pattern=file_pattern,
            exclude_dirs=exclude_dirs,
            fast_mode=fast_mode,
            compare_content=compare_content,
            min_duplicate_group=min_duplicate_group,
            max_results=max_results,
        )
        return _sanitize_for_json(result)

    return duplicate_finder_wrapper


def create_integrity_checker_wrapper(tool_instance):
    """Create a wrapper for the integrity checker tool."""

    async def integrity_checker_wrapper(
        paths: list,
        database: str = "~/.fastsearch/integrity_db.json",
        algorithm: str = "sha256",
        update: bool = False,
        recursive: bool = True,
        patterns: list = None,
        exclude_dirs: list = None,
        max_file_size: int = 100,
    ):
        """Check the integrity of files by verifying their checksums"""
        result = await tool_instance.execute(
            paths=paths,
            database=database,
            algorithm=algorithm,
            update=update,
            recursive=recursive,
            patterns=patterns,
            exclude_dirs=exclude_dirs,
            max_file_size=max_file_size,
        )
        return _sanitize_for_json(result)

    return integrity_checker_wrapper


def create_resource_monitor_wrapper(tool_instance):
    """Create a wrapper for the resource monitor tool."""

    async def resource_monitor_wrapper(
        interval: float = 1.0,
        duration: float = 0,
        include_processes: bool = True,
        process_limit: int = 10,
        include_cpu: bool = True,
        include_memory: bool = True,
        include_disk: bool = True,
        include_network: bool = True,
        include_system: bool = True,
        callback_url: str = None,
    ):
        """Monitor system resources including CPU, memory, disk, and network usage"""
        result = await tool_instance.execute(
            interval=interval,
            duration=duration,
            include_processes=include_processes,
            process_limit=process_limit,
            include_cpu=include_cpu,
            include_memory=include_memory,
            include_disk=include_disk,
            include_network=include_network,
            include_system=include_system,
            callback_url=callback_url,
        )
        return _sanitize_for_json(result)

    return resource_monitor_wrapper


def create_process_info_wrapper(tool_instance):
    """Create a wrapper for the process info tool."""

    async def process_info_wrapper(
        pids: list = None,
        name: str = None,
        user: str = None,
        limit: int = 100,
        sort_by: str = "cpu_percent",
        sort_desc: bool = True,
    ):
        """Get detailed information about running processes"""
        result = await tool_instance.execute(
            pids=pids, name=name, user=user, limit=limit, sort_by=sort_by, sort_desc=sort_desc
        )
        return _sanitize_for_json(result)

    return process_info_wrapper


def create_list_services_wrapper(tool_instance):
    """Create a wrapper for the list services tool."""

    async def list_services_wrapper(
        status: str = "all",
        startup_type: str = "all",
        search: str = "",
        include_details: bool = True,
    ):
        """List all Windows services with their status and details"""
        result = await tool_instance.execute(
            status=status, startup_type=startup_type, search=search, include_details=include_details
        )
        return _sanitize_for_json(result)

    return list_services_wrapper


def create_get_service_wrapper(tool_instance):
    """Create a wrapper for the get service tool."""

    async def get_service_wrapper(service_name: str):
        """Get detailed information about a specific Windows service"""
        result = await tool_instance.execute(service_name=service_name)
        return _sanitize_for_json(result)

    return get_service_wrapper


def create_start_service_wrapper(tool_instance):
    """Create a wrapper for the start service tool."""

    async def start_service_wrapper(service_name: str, args: list = None, timeout: int = 30):
        """Start a Windows service"""
        result = await tool_instance.execute(service_name=service_name, args=args, timeout=timeout)
        return _sanitize_for_json(result)

    return start_service_wrapper


def create_stop_service_wrapper(tool_instance):
    """Create a wrapper for the stop service tool."""

    async def stop_service_wrapper(service_name: str, timeout: int = 30):
        """Stop a Windows service"""
        result = await tool_instance.execute(service_name=service_name, timeout=timeout)
        return _sanitize_for_json(result)

    return stop_service_wrapper


def create_restart_service_wrapper(tool_instance):
    """Create a wrapper for the restart service tool."""

    async def restart_service_wrapper(service_name: str, timeout: int = 60):
        """Restart a Windows service"""
        result = await tool_instance.execute(service_name=service_name, timeout=timeout)
        return _sanitize_for_json(result)

    return restart_service_wrapper


def create_set_startup_type_wrapper(tool_instance):
    """Create a wrapper for the set startup type tool."""

    async def set_startup_type_wrapper(service_name: str, startup_type: str):
        """Set the startup type for a Windows service"""
        result = await tool_instance.execute(service_name=service_name, startup_type=startup_type)
        return _sanitize_for_json(result)

    return set_startup_type_wrapper


def create_get_logs_wrapper(tool_instance):
    """Create a wrapper for the get service logs tool."""

    async def get_logs_wrapper(
        service_name: str,
        log_type: str = "system",
        source: str = "",
        last: str = "1h",
        limit: int = 50,
        event_level: str = "all",
    ):
        """Get event logs for a Windows service"""
        result = await tool_instance.execute(
            service_name=service_name,
            log_type=log_type,
            source=source,
            last=last,
            limit=limit,
            event_level=event_level,
        )
        return _sanitize_for_json(result)

    return get_logs_wrapper


# Mapping of tool names to their wrapper creators
TOOL_WRAPPERS = {
    "help": create_help_wrapper,
    "fastsearch.search": create_file_name_search_wrapper,  # Simple file name search
    "fastsearch.search_advanced": create_advanced_search_wrapper,  # Advanced MFT search
    "file_content_search": create_file_search_wrapper,
    "analyze_disk_usage": create_disk_analyzer_wrapper,
    "drive_inventory": create_drive_inventory_wrapper,
    "find_duplicate_files": create_duplicate_finder_wrapper,
    "check_file_integrity": create_integrity_checker_wrapper,
    "monitor_system_resources": create_resource_monitor_wrapper,
    "get_process_info": create_process_info_wrapper,
    "list_services": create_list_services_wrapper,
    "get_service": create_get_service_wrapper,
    "start_service": create_start_service_wrapper,
    "stop_service": create_stop_service_wrapper,
    "restart_service": create_restart_service_wrapper,
    "set_service_startup_type": create_set_startup_type_wrapper,
    "get_service_logs": create_get_logs_wrapper,
}
