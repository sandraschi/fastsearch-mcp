"""
Tool wrappers for FastMCP 2.12 compatibility.

This module provides individual wrapper functions for each tool to ensure
FastMCP compatibility by avoiding **kwargs signatures.
"""

from typing import Dict, List, Any, Optional


def create_help_wrapper(tool_instance):
    """Create a wrapper for the help tool."""
    async def help_wrapper(tool_name: str = None):
        """Get help for available tools"""
        return await tool_instance.execute(tool_name=tool_name)
    return help_wrapper


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
        skip_binary: bool = True
    ):
        """Search for text patterns in files"""
        return await tool_instance.execute(
            search_pattern=search_pattern,
            search_dir=search_dir,
            file_pattern=file_pattern,
            exclude_dirs=exclude_dirs,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            max_results=max_results,
            context_lines=context_lines,
            max_file_size_mb=max_file_size_mb,
            skip_binary=skip_binary
        )
    return file_search_wrapper


def create_disk_analyzer_wrapper(tool_instance):
    """Create a wrapper for the disk analyzer tool."""
    async def disk_analyzer_wrapper(
        path: str = "/",
        max_depth: int = 3,
        include_partitions: bool = True,
        find_large_files: bool = True,
        large_file_limit: int = 50,
        min_file_size_mb: int = 10
    ):
        """Analyze disk usage and find large files and directories"""
        return await tool_instance.execute(
            path=path,
            max_depth=max_depth,
            include_partitions=include_partitions,
            find_large_files=find_large_files,
            large_file_limit=large_file_limit,
            min_file_size_mb=min_file_size_mb
        )
    return disk_analyzer_wrapper


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
        max_results: int = 100
    ):
        """Find duplicate files based on content hashing"""
        return await tool_instance.execute(
            search_dir=search_dir,
            min_size=min_size,
            max_size=max_size,
            file_pattern=file_pattern,
            exclude_dirs=exclude_dirs,
            fast_mode=fast_mode,
            compare_content=compare_content,
            min_duplicate_group=min_duplicate_group,
            max_results=max_results
        )
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
        max_file_size: int = 100
    ):
        """Check the integrity of files by verifying their checksums"""
        return await tool_instance.execute(
            paths=paths,
            database=database,
            algorithm=algorithm,
            update=update,
            recursive=recursive,
            patterns=patterns,
            exclude_dirs=exclude_dirs,
            max_file_size=max_file_size
        )
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
        callback_url: str = None
    ):
        """Monitor system resources including CPU, memory, disk, and network usage"""
        return await tool_instance.execute(
            interval=interval,
            duration=duration,
            include_processes=include_processes,
            process_limit=process_limit,
            include_cpu=include_cpu,
            include_memory=include_memory,
            include_disk=include_disk,
            include_network=include_network,
            include_system=include_system,
            callback_url=callback_url
        )
    return resource_monitor_wrapper


def create_process_info_wrapper(tool_instance):
    """Create a wrapper for the process info tool."""
    async def process_info_wrapper(
        pids: list = None,
        name: str = None,
        user: str = None,
        limit: int = 100,
        sort_by: str = "cpu_percent",
        sort_desc: bool = True
    ):
        """Get detailed information about running processes"""
        return await tool_instance.execute(
            pids=pids,
            name=name,
            user=user,
            limit=limit,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
    return process_info_wrapper


def create_list_services_wrapper(tool_instance):
    """Create a wrapper for the list services tool."""
    async def list_services_wrapper(
        status: str = "all",
        startup_type: str = "all",
        search: str = "",
        include_details: bool = True
    ):
        """List all Windows services with their status and details"""
        return await tool_instance.execute(
            status=status,
            startup_type=startup_type,
            search=search,
            include_details=include_details
        )
    return list_services_wrapper


def create_get_service_wrapper(tool_instance):
    """Create a wrapper for the get service tool."""
    async def get_service_wrapper(service_name: str):
        """Get detailed information about a specific Windows service"""
        return await tool_instance.execute(service_name=service_name)
    return get_service_wrapper


def create_start_service_wrapper(tool_instance):
    """Create a wrapper for the start service tool."""
    async def start_service_wrapper(
        service_name: str,
        args: list = None,
        timeout: int = 30
    ):
        """Start a Windows service"""
        return await tool_instance.execute(
            service_name=service_name,
            args=args,
            timeout=timeout
        )
    return start_service_wrapper


def create_stop_service_wrapper(tool_instance):
    """Create a wrapper for the stop service tool."""
    async def stop_service_wrapper(
        service_name: str,
        timeout: int = 30
    ):
        """Stop a Windows service"""
        return await tool_instance.execute(
            service_name=service_name,
            timeout=timeout
        )
    return stop_service_wrapper


def create_restart_service_wrapper(tool_instance):
    """Create a wrapper for the restart service tool."""
    async def restart_service_wrapper(
        service_name: str,
        timeout: int = 60
    ):
        """Restart a Windows service"""
        return await tool_instance.execute(
            service_name=service_name,
            timeout=timeout
        )
    return restart_service_wrapper


def create_set_startup_type_wrapper(tool_instance):
    """Create a wrapper for the set startup type tool."""
    async def set_startup_type_wrapper(
        service_name: str,
        startup_type: str
    ):
        """Set the startup type for a Windows service"""
        return await tool_instance.execute(
            service_name=service_name,
            startup_type=startup_type
        )
    return set_startup_type_wrapper


def create_get_logs_wrapper(tool_instance):
    """Create a wrapper for the get service logs tool."""
    async def get_logs_wrapper(
        service_name: str,
        log_type: str = "system",
        source: str = "",
        last: str = "1h",
        limit: int = 50,
        event_level: str = "all"
    ):
        """Get event logs for a Windows service"""
        return await tool_instance.execute(
            service_name=service_name,
            log_type=log_type,
            source=source,
            last=last,
            limit=limit,
            event_level=event_level
        )
    return get_logs_wrapper


# Mapping of tool names to their wrapper creators
TOOL_WRAPPERS = {
    "help": create_help_wrapper,
    "file_content_search": create_file_search_wrapper,
    "analyze_disk_usage": create_disk_analyzer_wrapper,
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
