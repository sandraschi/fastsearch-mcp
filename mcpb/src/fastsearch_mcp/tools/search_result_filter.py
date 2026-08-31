"""
Search result filtering tool for FastSearch MCP.

Further filters already-obtained search results by size, date, file type,
path patterns, and other criteria. Operates in memory without additional
searches.
"""

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastsearch_mcp.mcp_instance import mcp

logger = logging.getLogger(__name__)


def _parse_date(date_str: str) -> float | None:
    """Parse date string to timestamp."""
    if not date_str:
        return None
    try:
        # Try ISO format
        if date_str.endswith("Z"):
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(date_str)
        return dt.timestamp()
    except Exception:
        # Try relative time (e.g., "7d", "1h", "30m")
        date_lower = date_str.lower().strip()
        try:
            if date_lower.endswith("d"):
                days = int(date_lower[:-1])
                dt = datetime.now() - timedelta(days=days)
                return dt.timestamp()
            elif date_lower.endswith("h"):
                hours = int(date_lower[:-1])
                dt = datetime.now() - timedelta(hours=hours)
                return dt.timestamp()
            elif date_lower.endswith("m"):
                minutes = int(date_lower[:-1])
                dt = datetime.now() - timedelta(minutes=minutes)
                return dt.timestamp()
        except Exception:
            pass
    return None


def _matches_pattern(path: str, pattern: str) -> bool:
    """Check if path matches pattern (supports glob-like patterns)."""
    try:
        # Convert glob pattern to regex
        regex_pattern = pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".")
        return bool(re.search(regex_pattern, path, re.IGNORECASE))
    except Exception:
        return False


@mcp.tool
async def search_result_filter(
    results: list[dict[str, Any]],
    min_size: int | None = None,
    max_size: int | None = None,
    min_size_mb: float | None = None,
    max_size_mb: float | None = None,
    modified_after: str | None = None,
    modified_before: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    file_types: list[str] | None = None,
    path_pattern: str | None = None,
    exclude_path_pattern: str | None = None,
    min_depth: int | None = None,
    max_depth: int | None = None,
) -> dict[str, Any]:
    """Filter search results by various criteria without performing a new search.

    Further filters already-obtained search results by size, date ranges, file
    types, path patterns, and directory depth. This tool operates in memory on
    existing results and does not perform additional searches, making it fast
    for refining large result sets.

    Args:
        results: List of search result dictionaries from fastsearch_search or
            fastsearch_search_advanced to filter. Each result should contain at
            minimum a 'path' key. Required: List of dictionaries with file metadata.

        min_size: Minimum file size in bytes (default: None). Files smaller than
            this will be excluded. Examples: 1024, 1048576. Mutually exclusive
            with min_size_mb (use one or the other).

        max_size: Maximum file size in bytes (default: None). Files larger than
            this will be excluded. Examples: 10485760, 1073741824. Mutually
            exclusive with max_size_mb (use one or the other).

        min_size_mb: Minimum file size in megabytes (alternative to min_size)
            (default: None). More convenient than bytes for large files.
            Examples: 1.0, 100.5. Mutually exclusive with min_size.

        max_size_mb: Maximum file size in megabytes (alternative to max_size)
            (default: None). More convenient than bytes for large files.
            Examples: 10.0, 500.0. Mutually exclusive with max_size.

        modified_after: Only include files modified after this date
            (default: None). Supports ISO format (2024-01-01) or relative
            (7d, 1h, 30m). Examples: "2024-01-01", "7d", "1h", "30m".

        modified_before: Only include files modified before this date
            (default: None). Supports ISO format or relative time. Examples:
            "2024-12-31", "30d".

        created_after: Only include files created after this date
            (default: None). Supports ISO format or relative time. Examples:
            "2024-01-01", "7d".

        created_before: Only include files created before this date
            (default: None). Supports ISO format or relative time. Examples:
            "2024-12-31", "365d".

        file_types: List of file extensions to include (default: None).
            Case-insensitive. If None, includes all types. Examples:
            ['.txt', '.log'], ['.py', '.js', '.ts']. Extensions can include
            or omit the leading dot.

        path_pattern: Include only paths matching this pattern (glob-like)
            (default: None). Supports wildcards: * (any chars), ? (single char).
            Examples: '*temp*', 'C:\\Windows\\*', '*\\logs\\*'.

        exclude_path_pattern: Exclude paths matching this pattern (default: None).
            Applied after path_pattern filtering. Supports glob-like patterns.
            Examples: '*\\temp\\*', '*cache*'.

        min_depth: Minimum directory depth (default: None). Depth 0 = root,
            1 = one level deep. Files at shallower depths are excluded.
            Examples: 0, 2, 5.

        max_depth: Maximum directory depth (default: None). Files at deeper
            depths are excluded. Examples: 3, 10.

    Returns:
        Dictionary containing:
            success: Boolean indicating operation success. True if filtering completed
                successfully, False if an error occurred.

            filtered_results: List of filtered search result dictionaries. Contains
                only the results that passed all applied filters. Each result has the
                same structure as the input results (path, size, modified, created, etc.).

            count: Number of results after filtering (integer). Total number of
                results that passed all filters.

            original_count: Number of results before filtering (integer). Total number
                of results in the input results list.

            filters_applied: List of filters that were applied. Contains strings
                describing active filters (e.g., ["size", "modified_date", "file_types",
                "path_pattern"]). Useful for understanding what filters affected the results.

            error: Error message if success is False. Describes what went wrong and
                may include suggestions for resolution.

    Usage:
        This tool is used when you need to refine search results without
        performing a new search. It works by applying filters in memory to
        existing results. Best practices include:
        - Filter by size to find large or small files
        - Filter by date to find recent or old files
        - Filter by file type to focus on specific formats
        - Combine multiple filters for precise results

        Common scenarios:
        - Find large files modified recently
        - Filter to specific file types in certain directories
        - Exclude temporary or cache directories
        - Limit results to specific directory depths

    Examples:
        Filter by size:
            results = await fastsearch_search("*.log", path="C:\\Windows")
            filtered = await search_result_filter(
                results["results"],
                min_size_mb=1.0,
                max_size_mb=100.0
            )
            # Returns files between 1MB and 100MB

        Filter by date:
            filtered = await search_result_filter(
                results["results"],
                modified_after="7d"  # Last 7 days
            )
            # Returns files modified in the last week

        Filter by file type and path:
            filtered = await search_result_filter(
                results["results"],
                file_types=[".log", ".txt"],
                path_pattern="*temp*"
            )
            # Returns .log and .txt files in paths containing 'temp'

        Complex filtering:
            filtered = await search_result_filter(
                results["results"],
                min_size_mb=10.0,
                modified_after="30d",
                file_types=[".log"],
                exclude_path_pattern="*\\cache\\*"
            )
            # Returns large log files modified recently, excluding cache dirs

    Errors:
        Common errors and solutions:
        - No results to filter: Ensure results list is not empty before calling
        - Invalid date format: Use ISO format (YYYY-MM-DD) or relative (7d, 1h, 30m)
        - Invalid size values: Ensure size values are positive numbers
        - Pattern matching fails: Check glob pattern syntax (* and ? wildcards)

    See Also:
        - fastsearch_search: Generate search results to filter
        - fastsearch_search_advanced: Advanced search with filters
        - search_result_export: Export filtered results
        - search_result_analyze: Analyze filtered results
    """
    try:
        if not results:
            return {
                "success": True,
                "filtered_results": [],
                "count": 0,
                "original_count": 0,
                "filters_applied": [],
            }

        original_count = len(results)
        filtered_results = []
        filters_applied = []

        # Convert size filters to bytes
        min_size_bytes = min_size
        if min_size_mb is not None:
            min_size_bytes = int(min_size_mb * 1024 * 1024)
        if min_size_bytes is None:
            min_size_bytes = 0

        max_size_bytes = max_size
        if max_size_mb is not None:
            max_size_bytes = int(max_size_mb * 1024 * 1024)

        # Parse date filters
        modified_after_ts = _parse_date(modified_after) if modified_after else None
        modified_before_ts = _parse_date(modified_before) if modified_before else None
        created_after_ts = _parse_date(created_after) if created_after else None
        created_before_ts = _parse_date(created_before) if created_before else None

        # Normalize file types
        file_types_normalized = None
        if file_types:
            file_types_normalized = [ft.lower().lstrip(".") for ft in file_types]
            filters_applied.append(f"file_types: {file_types}")

        # Apply filters
        for result in results:
            path = result.get("path", "")
            size = result.get("size", 0)
            modified = result.get("modified")
            created = result.get("created")

            # Size filter
            if min_size_bytes > 0 or max_size_bytes:
                if isinstance(size, (int, float)):
                    size_int = int(size)
                    if min_size_bytes > 0 and size_int < min_size_bytes:
                        continue
                    if max_size_bytes and size_int > max_size_bytes:
                        continue
                    if min_size_bytes > 0 or max_size_bytes:
                        if "size" not in filters_applied:
                            filters_applied.append("size")

            # Date filters
            if modified_after_ts or modified_before_ts:
                if modified:
                    try:
                        if isinstance(modified, str):
                            if modified.endswith("Z"):
                                dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                            else:
                                dt = datetime.fromisoformat(modified)
                            modified_ts = dt.timestamp()
                        elif isinstance(modified, (int, float)):
                            modified_ts = float(modified)
                        else:
                            modified_ts = None

                        if modified_ts:
                            if modified_after_ts and modified_ts < modified_after_ts:
                                continue
                            if modified_before_ts and modified_ts > modified_before_ts:
                                continue
                            if "modified_date" not in filters_applied:
                                filters_applied.append("modified_date")
                    except Exception:
                        pass  # Skip if date parsing fails

            if created_after_ts or created_before_ts:
                if created:
                    try:
                        if isinstance(created, str):
                            if created.endswith("Z"):
                                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                            else:
                                dt = datetime.fromisoformat(created)
                            created_ts = dt.timestamp()
                        elif isinstance(created, (int, float)):
                            created_ts = float(created)
                        else:
                            created_ts = None

                        if created_ts:
                            if created_after_ts and created_ts < created_after_ts:
                                continue
                            if created_before_ts and created_ts > created_before_ts:
                                continue
                            if "created_date" not in filters_applied:
                                filters_applied.append("created_date")
                    except Exception:
                        pass

            # File type filter
            if file_types_normalized:
                try:
                    ext = Path(path).suffix.lower().lstrip(".")
                    if ext not in file_types_normalized:
                        continue
                except Exception:
                    continue

            # Path pattern filter
            if path_pattern:
                if not _matches_pattern(path, path_pattern):
                    continue
                if "path_pattern" not in filters_applied:
                    filters_applied.append(f"path_pattern: {path_pattern}")

            if exclude_path_pattern:
                if _matches_pattern(path, exclude_path_pattern):
                    continue
                if "exclude_path_pattern" not in filters_applied:
                    filters_applied.append(f"exclude_path_pattern: {exclude_path_pattern}")

            # Depth filter
            if min_depth is not None or max_depth is not None:
                try:
                    depth = len(Path(path).parts) - 1  # Subtract 1 for filename
                    if min_depth is not None and depth < min_depth:
                        continue
                    if max_depth is not None and depth > max_depth:
                        continue
                    if "depth" not in filters_applied:
                        filters_applied.append(f"depth: {min_depth or 0}-{max_depth or 'unlimited'}")
                except Exception:
                    pass

            # All filters passed
            filtered_results.append(result)

        logger.info(
            f"Filtered {original_count} results to {len(filtered_results)} results "
            f"({len(filters_applied)} filters applied)"
        )

        return {
            "success": True,
            "filtered_results": filtered_results,
            "count": len(filtered_results),
            "original_count": original_count,
            "filters_applied": filters_applied,
        }

    except Exception as e:
        logger.error(f"Error filtering search results: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to filter search results: {e!s}",
            "filtered_results": [],
            "count": 0,
            "original_count": len(results) if results else 0,
        }
