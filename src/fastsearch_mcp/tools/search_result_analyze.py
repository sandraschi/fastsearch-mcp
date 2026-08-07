"""
Search result analysis tool for FastSearch MCP.

Analyzes patterns in search results to provide actionable insights including
file type distribution, size statistics, location patterns, and date analysis.
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from fastsearch_mcp.mcp_instance import mcp

logger = logging.getLogger(__name__)


def _get_file_extension(path: str) -> str:
    """Extract file extension from path."""
    try:
        return Path(path).suffix.lower() or "(no extension)"
    except Exception:
        return "(unknown)"


def _get_directory(path: str) -> str:
    """Extract directory from path."""
    try:
        return str(Path(path).parent)
    except Exception:
        return "(unknown)"


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


@mcp.tool
async def search_result_analyze(
    results: list[dict[str, Any]],
    include_file_types: bool = True,
    include_size_stats: bool = True,
    include_location_patterns: bool = True,
    include_date_patterns: bool = True,
    top_n: int = 10,
) -> dict[str, Any]:
    """Analyze patterns in search results to provide actionable insights.

    Transforms raw search results into structured insights including file type
    distribution, size statistics, location patterns, and date analysis. This
    tool operates on search results (post-processing) and does not perform
    additional searches.

    Args:
        results: List of search result dictionaries. Each result should contain
            at minimum a 'path' key. Optional keys: 'size', 'modified', 'created',
            'attributes'. Results from fastsearch_search or fastsearch_search_advanced.
        include_file_types: Include file type distribution analysis (default: True)
        include_size_stats: Include size statistics analysis (default: True)
        include_location_patterns: Include location/directory pattern analysis (default: True)
        include_date_patterns: Include date pattern analysis (default: True)
        top_n: Number of top items to include in each category (default: 10)

    Returns:
        Dictionary containing:
            success: Boolean indicating operation success. True if analysis completed
                successfully, False if an error occurred.

            total_files: Total number of files analyzed (integer). Total count of
                results in the input results list.

            total_size: Total size of all files in bytes (integer). Sum of all file
                sizes from the results. Useful for understanding total disk usage.

            file_types: File type distribution dictionary (only if include_file_types=True).
                Maps file extensions to counts and percentages. Example:
                {".log": {"count": 50, "percentage": 33.3}, ".txt": {"count": 30, "percentage": 20.0}}.

            size_stats: Size statistics dictionary (only if include_size_stats=True).
                Contains: total, average, min, max, median file sizes in bytes.
                Example: {"total": 104857600, "average": 1048576, "min": 1024, "max": 10485760, "median": 524288}.

            location_patterns: Location/directory patterns dictionary (only if
                include_location_patterns=True). Contains top directories by count
                and by size. Example: {"top_by_count": [{"path": "C:\\Logs", "count": 50}],
                "top_by_size": [{"path": "C:\\Data", "size": 104857600}]}.

            date_patterns: Date analysis dictionary (only if include_date_patterns=True).
                Contains oldest/newest files and date spans. Example:
                {"oldest": "2024-01-01", "newest": "2024-12-31", "span_days": 365}.

            insights: List of actionable insights and recommendations (list of strings).
                Provides suggestions based on the analysis results. Example:
                ["Large files found in temp directory - consider cleanup",
                 "Many log files older than 30 days - consider archiving"].

            error: Error message if success is False. Describes what went wrong and
                may include suggestions for resolution.

    Examples:
        Basic usage:
            results = await fastsearch_search("*.log", path="C:\\Windows")
            analysis = await search_result_analyze(results["results"])
            # Returns: {'success': True, 'total_files': 150, 'file_types': {...}, ...}

        With specific analysis types:
            analysis = await search_result_analyze(
                results["results"],
                include_date_patterns=False,
                top_n=5
            )
    """
    try:
        if not results:
            return {
                "success": True,
                "total_files": 0,
                "total_size": 0,
                "message": "No results to analyze",
                "file_types": {},
                "size_stats": {},
                "location_patterns": {},
                "date_patterns": {},
                "insights": [],
            }

        total_files = len(results)
        total_size = 0
        extensions = Counter()
        directories = Counter()
        sizes = []
        modified_dates = []
        created_dates = []
        directory_sizes = defaultdict(int)

        # Process each result
        for result in results:
            path = result.get("path", "")
            size = result.get("size", 0)
            modified = result.get("modified")
            created = result.get("created")

            # File type analysis
            if include_file_types and path:
                ext = _get_file_extension(path)
                extensions[ext] += 1

            # Size analysis
            if include_size_stats:
                if isinstance(size, (int, float)) and size > 0:
                    total_size += int(size)
                    sizes.append(int(size))
                    if include_location_patterns:
                        dir_path = _get_directory(path)
                        directory_sizes[dir_path] += int(size)

            # Location analysis
            if include_location_patterns and path:
                dir_path = _get_directory(path)
                directories[dir_path] += 1

            # Date analysis
            if include_date_patterns:
                if modified:
                    try:
                        if isinstance(modified, str):
                            # Try parsing ISO format or timestamp
                            if modified.endswith("Z"):
                                dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                            else:
                                dt = datetime.fromisoformat(modified)
                            modified_dates.append(dt.timestamp())
                        elif isinstance(modified, (int, float)):
                            modified_dates.append(float(modified))
                    except Exception:
                        pass

                if created:
                    try:
                        if isinstance(created, str):
                            if created.endswith("Z"):
                                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                            else:
                                dt = datetime.fromisoformat(created)
                            created_dates.append(dt.timestamp())
                        elif isinstance(created, (int, float)):
                            created_dates.append(float(created))
                    except Exception:
                        pass

        # Build analysis results
        analysis: dict[str, Any] = {
            "success": True,
            "total_files": total_files,
            "total_size": total_size,
            "total_size_formatted": _format_size(total_size),
        }

        # File type distribution
        if include_file_types:
            file_types = {
                "distribution": dict(extensions.most_common(top_n)),
                "total_types": len(extensions),
                "most_common": extensions.most_common(1)[0][0] if extensions else None,
            }
            analysis["file_types"] = file_types

        # Size statistics
        if include_size_stats:
            if sizes:
                sizes_sorted = sorted(sizes)
                size_stats = {
                    "total": total_size,
                    "total_formatted": _format_size(total_size),
                    "average": int(sum(sizes) / len(sizes)),
                    "average_formatted": _format_size(int(sum(sizes) / len(sizes))),
                    "min": min(sizes),
                    "min_formatted": _format_size(min(sizes)),
                    "max": max(sizes),
                    "max_formatted": _format_size(max(sizes)),
                    "median": sizes_sorted[len(sizes_sorted) // 2],
                    "median_formatted": _format_size(sizes_sorted[len(sizes_sorted) // 2]),
                }
            else:
                size_stats = {
                    "total": 0,
                    "total_formatted": "0 B",
                    "average": 0,
                    "average_formatted": "0 B",
                    "min": 0,
                    "max": 0,
                    "median": 0,
                }
            analysis["size_stats"] = size_stats

        # Location patterns
        if include_location_patterns:
            top_dirs = directories.most_common(top_n)
            top_dirs_by_size = []
            if directory_sizes:
                top_dirs_by_size = sorted(directory_sizes.items(), key=lambda x: x[1], reverse=True)[:top_n]

            location_patterns = {
                "top_directories_by_count": [
                    {"directory": dir_path, "file_count": count} for dir_path, count in top_dirs
                ],
                "top_directories_by_size": [
                    {
                        "directory": dir_path,
                        "total_size": size,
                        "total_size_formatted": _format_size(size),
                    }
                    for dir_path, size in top_dirs_by_size
                ],
                "unique_directories": len(directories),
            }
            analysis["location_patterns"] = location_patterns

        # Date patterns
        if include_date_patterns:
            date_patterns: dict[str, Any] = {}
            if modified_dates:
                modified_dates_sorted = sorted(modified_dates)
                oldest_modified = datetime.fromtimestamp(modified_dates_sorted[0])
                newest_modified = datetime.fromtimestamp(modified_dates_sorted[-1])
                date_patterns["modified"] = {
                    "oldest": oldest_modified.isoformat(),
                    "newest": newest_modified.isoformat(),
                    "span_days": (newest_modified - oldest_modified).days,
                }

            if created_dates:
                created_dates_sorted = sorted(created_dates)
                oldest_created = datetime.fromtimestamp(created_dates_sorted[0])
                newest_created = datetime.fromtimestamp(created_dates_sorted[-1])
                date_patterns["created"] = {
                    "oldest": oldest_created.isoformat(),
                    "newest": newest_created.isoformat(),
                    "span_days": (newest_created - oldest_created).days,
                }

            analysis["date_patterns"] = date_patterns if date_patterns else {}

        # Generate insights
        insights = []
        if include_file_types and extensions:
            most_common_ext = extensions.most_common(1)[0]
            if most_common_ext[1] > total_files * 0.5:
                ext_name = most_common_ext[0]
                ext_count = most_common_ext[1]
                insights.append(f"Most files ({ext_count}/{total_files}) are {ext_name} files")

        if include_size_stats and sizes:
            if total_size > 1024 * 1024 * 1024:  # > 1GB
                insights.append(f"Total size is {_format_size(total_size)} - consider cleanup")
            largest_files = sorted(sizes, reverse=True)[:3]
            if largest_files and largest_files[0] > 100 * 1024 * 1024:  # > 100MB
                insights.append(f"Largest files are {_format_size(largest_files[0])} - review for optimization")

        if include_location_patterns and directories:
            top_dir = directories.most_common(1)[0]
            if top_dir[1] > total_files * 0.3:
                insights.append(f"Most files ({top_dir[1]}/{total_files}) are in {top_dir[0]}")

        if include_date_patterns and modified_dates:
            oldest = datetime.fromtimestamp(min(modified_dates))
            days_old = (datetime.now() - oldest).days
            if days_old > 365:
                insights.append(f"Oldest file is {days_old} days old - consider archiving")

        analysis["insights"] = insights

        logger.info(f"Analyzed {total_files} search results")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing search results: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to analyze search results: {e!s}",
            "total_files": 0,
            "total_size": 0,
        }
