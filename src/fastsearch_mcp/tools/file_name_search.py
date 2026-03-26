"""Simple file name search tool for MCP."""

import asyncio
import logging
from typing import Any, Dict, List

try:
    import psutil
except ImportError:
    psutil = None

from fastsearch_mcp.mcp_instance import mcp
from fastsearch_mcp.service_client import search_files

logger = logging.getLogger(__name__)


def _get_ntfs_drives() -> List[str]:
    """Get all NTFS drive letters on the system."""
    drives = []
    if psutil:
        try:
            for partition in psutil.disk_partitions(all=False):
                if partition.fstype and "ntfs" in partition.fstype.lower():
                    # Extract drive letter from mountpoint (e.g., "C:\\" -> "C:\\")
                    mountpoint = partition.mountpoint
                    if mountpoint and len(mountpoint) >= 2:
                        # Ensure it ends with backslash
                        if not mountpoint.endswith("\\"):
                            mountpoint += "\\"
                        drives.append(mountpoint)
        except Exception as e:
            logger.warning(f"Error detecting NTFS drives: {e}")
    else:
        # Fallback: try common drive letters
        import string

        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            try:
                from pathlib import Path

                if Path(drive).exists():
                    drives.append(drive)
            except Exception:
                pass

    # Default to C:\ if no drives found
    if not drives:
        drives = ["C:\\"]

    return drives


def _normalize_search_path(path: str) -> str:
    """Normalize path so the C++ service receives a format it accepts (e.g. C:\\ not C:)."""
    if not path or path in ("*", "all", "ALL"):
        return path
    path = path.strip()
    # Drive letter only: "C:", "C", "c" -> "C:\\"
    if len(path) <= 2:
        letter = path[0].upper() if path else ""
        if letter.isalpha() and (len(path) == 1 or path[1] == ":"):
            return f"{letter}:\\"
    # "X:" (exactly two chars) -> "X:\\"
    if len(path) == 2 and path[0].isalpha() and path[1] == ":":
        return f"{path[0].upper()}:\\"
    # Already has backslashes; ensure no leading/trailing spaces
    return path


@mcp.tool
async def fastsearch_search(
    pattern: str,
    path: str = "C:\\",
    search_all: bool = False,
    max_results: int = 100,
    pagination_mode: str = "none",
    page: int = 1,
    page_size: int = 1000,
) -> Dict[str, Any]:
    """Search for files by name pattern using direct NTFS MFT access.

    Simple and fast file name search using direct NTFS Master File Table access.
    Can search all NTFS drives at once. Provides instant results without indexing
    delays. This tool uses the WizFile philosophy - direct filesystem access,
    not traditional indexing.

    Note: This tool only searches NTFS drives. Non-NTFS drives (FAT32, exFAT, etc.)
    require treewalking which violates the direct MFT access architecture.

    Args:
        pattern: File name pattern to search for. Examples: '*.py', 'test*.txt',
            'README.md', '*.{log,txt}'. Supports glob patterns with wildcards.

        path: Directory to search in (default: "C:\\"). When a drive letter is
            specified (e.g., 'D:\\'), searches the entire drive. Use '*' to search
            all NTFS drives. Examples: "C:\\", "D:\\Projects", "*".

        search_all: Search all connected NTFS drives in one go (overrides path
            parameter) (default: False). When True, searches all NTFS drives and
            returns results grouped by drive. Default behavior searches only NTFS
            drives, skipping non-NTFS filesystems.

        max_results: Maximum number of results to return (default: 100). When
            search_all=True, this limit applies per drive. Use 0 for unlimited
            (capped at 10M for safety). Stops searching after finding this many results.
        
        pagination_mode: Pagination mode (default: "none"). Options:
            - "none": Return all results in single response (default)
            - "offset": Page-based pagination (use with page and page_size)
        
        page: Page number for offset pagination (default: 1, 1-indexed).
            Only used when pagination_mode="offset".
        
        page_size: Results per page for offset pagination (default: 1000).
            Only used when pagination_mode="offset". Maximum 100,000 per page.

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
                - attributes: File attributes (readonly, hidden, system, etc.)

            count: Number of results found (integer). Total number of files matching
                the pattern.

            drives_searched: List of drives searched (only if search_all=True).
                Contains drive letters that were searched. Example: ["C:\\", "D:\\"].

            drive_results: Results per drive (only if search_all=True). Dictionary
                mapping drive letters to result counts or error messages.

            method: Search method used. Always "ntfs_mft" for successful searches,
                "error" if search failed.

            error: Error message if success is False. Describes what went wrong and
                may include suggestions for resolution.

    Usage:
        This tool is used when you need to quickly find files by name pattern
        without waiting for indexing. It works by directly querying the NTFS
        Master File Table for each search. Best practices include:
        - Use glob patterns for flexible matching
        - Set max_results to limit result size
        - Use search_all for comprehensive multi-drive searches
        - Check service_status first to ensure FastSearch service is running

        Common scenarios:
        - Find all Python files in a directory
        - Search for specific file names across drives
        - Locate log files or configuration files
        - Find files matching a naming pattern

    Examples:
        Basic search:
            results = await fastsearch_search("*.py", path="C:\\Projects")
            # Returns: {'success': True, 'results': [...], 'count': 42}

        Search all drives:
            results = await fastsearch_search("*.log", search_all=True, max_results=50)
            # Returns: {'success': True, 'drives_searched': ['C:\\', 'D:\\'], ...}

        Search specific drive:
            results = await fastsearch_search("README.md", path="D:\\")
            # Returns: {'success': True, 'results': [...], 'count': 3}

        Paginated search (page 1):
            results = await fastsearch_search(
                "*.py",
                path="C:\\",
                max_results=0,  # Unlimited (capped at 10M)
                pagination_mode="offset",
                page=1,
                page_size=1000
            )
            # Returns: {'success': True, 'results': [...], 'count': 1000,
            #          'pagination': {'mode': 'offset', 'page': 1, 'page_size': 1000,
            #                        'total_pages': 5, 'total_results': 5000,
            #                        'has_next': True, 'has_previous': False}}

        Paginated search (page 2):
            results = await fastsearch_search(
                "*.py",
                path="C:\\",
                max_results=0,
                pagination_mode="offset",
                page=2,
                page_size=1000
            )
            # Returns page 2 of results

    Errors:
        Common errors and solutions:
        - Pattern is required: Provide a non-empty search pattern
        - Service not available: Use service_status to check service state,
          then use service_start_fastsearch if needed
        - Directory not found: Verify the path exists and is accessible
        - Timeout: Search exceeded 30 seconds per drive (try narrowing search scope)

    See Also:
        - fastsearch_search_advanced: Advanced search with size/date/attribute filters
        - file_content_search: Search within file contents
        - service_status: Check FastSearch service status
        - service_start_fastsearch: Start the FastSearch service if needed
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
            # Search all NTFS drives in parallel (load-balanced: one task per drive).
            # Each drive uses its own pipe connection; C++ service must accept multiple
            # pipe clients (standard NamedPipe server pattern).
            drives = _get_ntfs_drives()
            logger.info(f"Searching all NTFS drives in parallel ({len(drives)} drives) for pattern: {pattern}")

            async def search_one_drive(drive: str) -> tuple[str, dict]:
                try:
                    drive_result = await asyncio.wait_for(
                        search_files(
                            pattern=pattern,
                            directory=drive,
                            max_results=max_results,
                            pagination_mode=pagination_mode if pagination_mode != "none" else None,
                            page=page,
                            page_size=page_size,
                        ),
                        timeout=30.0,
                    )
                    if drive_result and drive_result.get("results"):
                        return drive, {"count": drive_result.get("count", 0), "results": drive_result["results"]}
                    return drive, {"count": 0, "results": []}
                except asyncio.TimeoutError:
                    logger.warning(f"Search on drive {drive} timed out after 30 seconds")
                    return drive, {"error": "Timeout after 30 seconds"}
                except Exception as e:
                    logger.warning(f"Error searching drive {drive}: {e}")
                    return drive, {"error": str(e)}

            results_per_drive = await asyncio.gather(*[search_one_drive(d) for d in drives])
            all_results = []
            drive_results = {}
            for drive, data in results_per_drive:
                if "error" in data:
                    drive_results[drive] = data
                else:
                    drive_results[drive] = data.get("count", 0)
                    all_results.extend(data.get("results", []))

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
            }
        else:
            # Search single path: normalize so C++ service gets e.g. C:\ not C:
            directory = _normalize_search_path(path)
            logger.info(f"Searching for files matching pattern: {pattern!r} in directory: {directory!r} (input path: {path!r})")

            # Use service_client.search_files which REQUIRES MFT service (no fallback)
            try:
                result = await search_files(
                    pattern=pattern,
                    directory=directory,
                    max_results=max_results,
                    pagination_mode=pagination_mode if pagination_mode != "none" else None,
                    page=page,
                    page_size=page_size,
                )
                
                # Extract results and pagination from service response
                results = result.get("results", []) if isinstance(result, dict) else result
                pagination = result.get("pagination") if isinstance(result, dict) else None
                
                return {
                    "success": True,
                    "pattern": pattern,
                    "path": path,
                    "results": results,
                    "count": result.get("count", len(results)) if isinstance(result, dict) else len(results),
                    "pagination": pagination,
                    "method": "ntfs_mft",
                }
            except RuntimeError as e:
                # Service not available - return error with helpful message
                error_msg = str(e)
                return {
                    "success": False,
                    "error": error_msg,
                    "pattern": pattern,
                    "path": path,
                    "results": [],
                    "count": 0,
                    "method": "error",
                    "service_required": True,
                    "suggestion": (
                        "The FastSearch service is required for file searches. "
                        "Use the 'service_status' tool to check if the service is running, "
                        "or use 'start_service' to start it if it's installed but stopped."
                    ),
                }

    except RuntimeError as e:
        # Service-related errors
        logger.error(f"MFT search failed (service unavailable): {e}")
        return {
            "success": False,
            "error": str(e),
            "pattern": pattern,
            "path": path,
            "results": [],
            "count": 0,
            "method": "error",
        }
    except Exception as e:
        logger.exception(f"File search failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "pattern": pattern,
            "path": path,
            "results": [],
            "count": 0,
            "method": "error",
        }
