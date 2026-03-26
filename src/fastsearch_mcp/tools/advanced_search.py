"""Advanced file search tool using all available NTFS MFT attributes."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import psutil
except ImportError:
    psutil = None

from fastsearch_mcp.mcp_instance import mcp
from fastsearch_mcp.pipe_client import NamedPipeClient
from fastsearch_mcp.service_client import is_service_running

logger = logging.getLogger(__name__)


def _ntfs_time_to_timestamp(ntfs_time: int) -> int:
    """Convert NTFS 100-nanosecond intervals since 1601-01-01 to Unix timestamp."""
    # NTFS epoch: 1601-01-01 00:00:00 UTC
    # Unix epoch: 1970-01-01 00:00:00 UTC
    # Difference: 11644473600 seconds = 116444736000000000 100-nanosecond intervals
    if ntfs_time == 0:
        return 0
    return (ntfs_time // 10000000) - 11644473600


def _parse_date_filter(date_str: str) -> Optional[int]:
    """Parse date string to NTFS timestamp (100-nanosecond intervals since 1601-01-01)."""
    if not date_str:
        return None

    try:
        # Try different date formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y",
        ]

        dt = None
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if dt is None:
            # Try relative time (e.g., "7d", "1h", "30m")
            date_lower = date_str.lower().strip()
            if date_lower.endswith("d"):
                days = int(date_lower[:-1])
                dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                from datetime import timedelta

                dt = dt - timedelta(days=days)
            elif date_lower.endswith("h"):
                hours = int(date_lower[:-1])
                dt = datetime.now().replace(minute=0, second=0, microsecond=0)
                from datetime import timedelta

                dt = dt - timedelta(hours=hours)
            elif date_lower.endswith("m"):
                minutes = int(date_lower[:-1])
                dt = datetime.now().replace(second=0, microsecond=0)
                from datetime import timedelta

                dt = dt - timedelta(minutes=minutes)
            else:
                return None

        # Convert to NTFS timestamp
        unix_timestamp = int(dt.timestamp())
        ntfs_timestamp = (unix_timestamp + 11644473600) * 10000000
        return ntfs_timestamp

    except Exception as e:
        logger.warning(f"Error parsing date '{date_str}': {e}")
        return None


def _get_ntfs_drives() -> List[str]:
    """Get all NTFS drive letters on the system."""
    drives = []
    if psutil:
        try:
            for partition in psutil.disk_partitions(all=False):
                if partition.fstype and "ntfs" in partition.fstype.lower():
                    mountpoint = partition.mountpoint
                    if mountpoint and len(mountpoint) >= 2:
                        if not mountpoint.endswith("\\"):
                            mountpoint += "\\"
                        drives.append(mountpoint)
        except Exception as e:
            logger.warning(f"Error detecting NTFS drives: {e}")
    else:
        import string

        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            try:
                from pathlib import Path

                if Path(drive).exists():
                    drives.append(drive)
            except Exception:
                pass

    if not drives:
        drives = ["C:\\"]

    return drives


async def _search_via_pipe_advanced(
    pattern: str,
    directory: str,
    max_results: int,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    modified_after: Optional[str] = None,
    modified_before: Optional[str] = None,
    accessed_after: Optional[str] = None,
    accessed_before: Optional[str] = None,
    include_directories: bool = False,
    include_readonly: bool = True,
    include_hidden: bool = False,
    include_system: bool = False,
    include_compressed: bool = True,
    include_encrypted: bool = True,
) -> List[Dict[str, Any]]:
    """Search files via named pipe with advanced filters."""
    if not is_service_running():
        logger.warning("FastSearch service is not running")
        return []

    try:
        async with NamedPipeClient() as client:
            if not client.connected:
                logger.warning("Could not connect to FastSearch service")
                return []

            # Build request with all filters
            request: Dict[str, Any] = {
                "command": "search_files",
                "pattern": pattern,
                "directory": directory,
                "max_results": max_results,
            }

            # Add size filters
            if min_size is not None:
                request["min_size"] = min_size
            if max_size is not None:
                request["max_size"] = max_size

            # Add timestamp filters (convert to NTFS timestamps)
            if created_after:
                ts = _parse_date_filter(created_after)
                if ts:
                    request["created_after"] = ts
            if created_before:
                ts = _parse_date_filter(created_before)
                if ts:
                    request["created_before"] = ts
            if modified_after:
                ts = _parse_date_filter(modified_after)
                if ts:
                    request["modified_after"] = ts
            if modified_before:
                ts = _parse_date_filter(modified_before)
                if ts:
                    request["modified_before"] = ts
            if accessed_after:
                ts = _parse_date_filter(accessed_after)
                if ts:
                    request["accessed_after"] = ts
            if accessed_before:
                ts = _parse_date_filter(accessed_before)
                if ts:
                    request["accessed_before"] = ts

            # Add file attribute filters
            request["include_directories"] = include_directories
            request["include_readonly"] = include_readonly
            request["include_hidden"] = include_hidden
            request["include_system"] = include_system
            request["include_compressed"] = include_compressed
            request["include_encrypted"] = include_encrypted

            response = await client.send_request(request)
            if response and response.get("success"):
                results = response.get("results", [])
                # Convert NTFS timestamps to Unix timestamps for readability
                for result in results:
                    for time_key in ["created", "modified", "accessed", "mft_modified"]:
                        if time_key in result and result[time_key]:
                            result[f"{time_key}_unix"] = _ntfs_time_to_timestamp(result[time_key])
                return results
            else:
                error_msg = response.get("error", "Unknown error") if response else "No response"
                logger.error(f"Advanced search failed: {error_msg}")
                return []

    except Exception as e:
        logger.exception(f"Error in advanced search: {e}")
        return []


@mcp.tool
async def fastsearch_search_advanced(
    pattern: str,
    path: str = "C:\\",
    search_all: bool = False,
    max_results: int = 100,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    modified_after: Optional[str] = None,
    modified_before: Optional[str] = None,
    accessed_after: Optional[str] = None,
    accessed_before: Optional[str] = None,
    include_directories: bool = False,
    include_readonly: bool = True,
    include_hidden: bool = False,
    include_system: bool = False,
    include_compressed: bool = True,
    include_encrypted: bool = True,
) -> Dict[str, Any]:
    """Advanced file search using all available NTFS MFT attributes.

    Comprehensive file search with filtering by size, timestamps, file attributes,
    and more. Uses direct NTFS Master File Table access for fast, real-time results.
    Can search all NTFS drives at once. Provides detailed metadata from NTFS MFT
    including all file attributes and timestamps.

    Args:
        pattern: File name pattern to search for. Examples: '*.py', 'test*.txt',
            'README.md', '*.{log,txt}'. Supports glob patterns with wildcards.

        path: Directory to search in (default: "C:\\"). When a drive letter is
            specified (e.g., 'D:\\'), searches the entire drive. Use '*' to search
            all NTFS drives. Examples: "C:\\", "D:\\Projects", "*".

        search_all: Search all connected NTFS drives in one go (overrides path
            parameter) (default: False). When True, searches all NTFS drives and
            returns results grouped by drive.

        max_results: Maximum number of results to return (default: 100). When
            search_all=True, this limit applies per drive. Stops searching after
            finding this many results.

        min_size: Minimum file size in bytes (default: None). Files smaller than
            this will be excluded. Examples: 1024, 1048576. Mutually exclusive
            with max_size for range filtering.

        max_size: Maximum file size in bytes (default: None). Files larger than
            this will be excluded. Examples: 10485760, 1073741824.

        created_after: Only include files created after this date (default: None).
            Supports ISO format (YYYY-MM-DD) or relative time (7d, 1h, 30m).
            Examples: "2024-01-01", "7d", "1h".

        created_before: Only include files created before this date (default: None).
            Supports ISO format or relative time. Examples: "2024-12-31", "30d".

        modified_after: Only include files modified after this date (default: None).
            Supports ISO format or relative time. Examples: "2024-01-01", "7d".

        modified_before: Only include files modified before this date (default: None).
            Supports ISO format or relative time. Examples: "2024-12-31", "30d".

        accessed_after: Only include files accessed after this date (default: None).
            Supports ISO format or relative time. Examples: "2024-01-01", "7d".

        accessed_before: Only include files accessed before this date (default: None).
            Supports ISO format or relative time. Examples: "2024-12-31", "30d".

        include_directories: Include directories in results (default: False).
            When True, directories matching the pattern are included.

        include_readonly: Include readonly files (default: True). When False,
            readonly files are excluded from results.

        include_hidden: Include hidden files (default: False). When True, hidden
            files are included in results.

        include_system: Include system files (default: False). When True, system
            files are included in results.

        include_compressed: Include compressed files (default: True). When False,
            compressed files are excluded from results.

        include_encrypted: Include encrypted files (default: True). When False,
            encrypted files are excluded from results.

    Returns:
        Dictionary containing:
            success: Boolean indicating operation success. True if search completed
                successfully, False if an error occurred.

            pattern: The search pattern used. Same as the input pattern parameter.

            path: The path searched. Contains the input path, or "all_ntfs_drives" if
                search_all=True. Examples: "C:\\", "D:\\Projects", "all_ntfs_drives".

            results: List of file result dictionaries. Each result contains:
                - path: Full absolute file path (e.g., "C:\\Users\\file.txt")
                - size: File size in bytes (integer)
                - modified: Modification timestamp (ISO format string or timestamp)
                - created: Creation timestamp (ISO format string or timestamp)
                - accessed: Access timestamp (ISO format string or timestamp)
                - attributes: File attributes dictionary with flags for readonly,
                  hidden, system, archive, compressed, encrypted, etc.

            count: Number of results found (integer). Total number of files matching
                the pattern and filters.

            drives_searched: List of drives searched (only if search_all=True).
                Contains drive letters that were searched. Example: ["C:\\", "D:\\"].

            drive_results: Results per drive (only if search_all=True). Dictionary
                mapping drive letters to result counts or error messages.

            filters_applied: List of filters that were applied. Contains strings
                describing active filters (e.g., ["size", "modified_date", "hidden"]).

            error: Error message if success is False. Describes what went wrong and
                may include suggestions for resolution.

    Usage:
        This tool is used when you need advanced filtering capabilities beyond
        simple name pattern matching. It works by directly querying the NTFS
        Master File Table and applying filters in real-time. Best practices include:
        - Combine multiple filters for precise results
        - Use date filters to find recent or old files
        - Filter by size to find large or small files
        - Use file attributes to include/exclude system files
        - Set max_results to limit result size

        Common scenarios:
        - Find large files modified recently
        - Search for files created in a date range
        - Find hidden or system files
        - Filter by file attributes (readonly, compressed, encrypted)
        - Multi-drive searches with comprehensive filtering

    Examples:
        Search with size filter:
            results = await fastsearch_search_advanced(
                "*.log",
                path="C:\\Windows",
                min_size=1048576,  # 1MB
                max_size=104857600  # 100MB
            )
            # Returns: {'success': True, 'results': [...], 'count': 15}

        Search with date filter:
            results = await fastsearch_search_advanced(
                "*.txt",
                modified_after="7d",  # Last 7 days
                include_hidden=True
            )
            # Returns: {'success': True, 'results': [...], 'count': 42}

        Complex multi-filter search:
            results = await fastsearch_search_advanced(
                "*.py",
                search_all=True,
                min_size=1024,
                modified_after="30d",
                include_readonly=False,
                include_system=False,
                max_results=200
            )
            # Returns: {'success': True, 'drives_searched': [...], ...}

    Errors:
        Common errors and solutions:
        - Pattern is required: Provide a non-empty search pattern
        - Service not available: Use service_status to check service state,
          then use service_start_fastsearch if needed
        - Invalid date format: Use ISO format (YYYY-MM-DD) or relative (7d, 1h, 30m)
        - Directory not found: Verify the path exists and is accessible
        - Invalid size values: Ensure size values are positive numbers

    See Also:
        - fastsearch_search: Simple name pattern search without filters
        - file_content_search: Search within file contents
        - search_result_filter: Further filter search results after finding files
        - service_status: Check FastSearch service status
    """
    if not pattern:
        return {
            "success": False,
            "error": "Pattern is required",
            "results": [],
            "count": 0,
        }

    try:
        # Determine if we should search all drives
        if search_all or path in ("*", "all", "ALL"):
            drives = _get_ntfs_drives()
            logger.info(
                f"Advanced search on all NTFS drives ({len(drives)} drives) "
                f"for pattern: {pattern}"
            )

            all_results = []
            drive_results = {}

            for drive in drives:
                try:
                    logger.debug(f"Searching drive {drive} with advanced filters")
                    # Add timeout per drive to prevent hanging (30 seconds per drive)
                    try:
                        drive_result = await asyncio.wait_for(
                            _search_via_pipe_advanced(
                                pattern=pattern,
                                directory=drive,
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
                            ),
                            timeout=30.0
                        )
                        if drive_result:
                            all_results.extend(drive_result)
                            drive_results[drive] = len(drive_result)
                        else:
                            drive_results[drive] = 0
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Advanced search on drive {drive} "
                            "timed out after 30 seconds"
                        )
                        drive_results[drive] = {"error": "Timeout after 30 seconds"}
                except Exception as e:
                    logger.warning(f"Error searching drive {drive}: {e}")
                    drive_results[drive] = {"error": str(e)}

            if len(all_results) > max_results:
                all_results = all_results[:max_results]

            return {
                "success": True,
                "pattern": pattern,
                "path": "all_ntfs_drives",
                "drives_searched": drives,
                "drive_results": drive_results,
                "results": all_results,
                "count": len(all_results),
                "filters_applied": {
                    "min_size": min_size,
                    "max_size": max_size,
                    "created_after": created_after,
                    "created_before": created_before,
                    "modified_after": modified_after,
                    "modified_before": modified_before,
                    "accessed_after": accessed_after,
                    "accessed_before": accessed_before,
                    "include_directories": include_directories,
                    "include_readonly": include_readonly,
                    "include_hidden": include_hidden,
                    "include_system": include_system,
                    "include_compressed": include_compressed,
                    "include_encrypted": include_encrypted,
                },
            }
        else:
            # Search single path
            logger.info(f"Advanced search for pattern: {pattern} in {path}")

            results = await _search_via_pipe_advanced(
                pattern=pattern,
                directory=path,
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

            return {
                "success": True,
                "pattern": pattern,
                "path": path,
                "results": results,
                "count": len(results),
                "filters_applied": {
                    "min_size": min_size,
                    "max_size": max_size,
                    "created_after": created_after,
                    "created_before": created_before,
                    "modified_after": modified_after,
                    "modified_before": modified_before,
                    "accessed_after": accessed_after,
                    "accessed_before": accessed_before,
                    "include_directories": include_directories,
                    "include_readonly": include_readonly,
                    "include_hidden": include_hidden,
                    "include_system": include_system,
                    "include_compressed": include_compressed,
                    "include_encrypted": include_encrypted,
                },
            }

    except Exception as e:
        logger.exception(f"Advanced search failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "pattern": pattern,
            "path": path,
            "results": [],
            "count": 0,
        }
