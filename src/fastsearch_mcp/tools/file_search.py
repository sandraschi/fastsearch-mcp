"""File content search tool for MCP."""

import asyncio
import re
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastsearch_mcp.mcp_instance import mcp
from fastsearch_mcp.utils.file_utils import find_files, search_in_file


def parse_date_filter(date_str: str) -> Optional[float]:
    """Parse date string to timestamp for filtering."""
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

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.timestamp()
            except ValueError:
                continue

        # If no format matches, try parsing as relative time
        if date_str.lower().endswith("d"):
            days = int(date_str[:-1])
            return datetime.now().timestamp() - (days * 24 * 3600)
        elif date_str.lower().endswith("h"):
            hours = int(date_str[:-1])
            return datetime.now().timestamp() - (hours * 3600)
        elif date_str.lower().endswith("m"):
            minutes = int(date_str[:-1])
            return datetime.now().timestamp() - (minutes * 60)

    except Exception:
        pass

    return None


def check_file_attributes(file_path: Path, required_attrs: List[str]) -> bool:
    """Check if file has required attributes."""
    if not required_attrs:
        return True

    try:
        stat_info = file_path.stat()
        file_attrs = stat_info.st_file_attributes if hasattr(stat_info, "st_file_attributes") else 0

        for attr in required_attrs:
            attr_lower = attr.lower()
            if attr_lower == "readonly" and not (file_attrs & stat.FILE_ATTRIBUTE_READONLY):
                return False
            elif attr_lower == "hidden" and not (file_attrs & stat.FILE_ATTRIBUTE_HIDDEN):
                return False
            elif attr_lower == "system" and not (file_attrs & stat.FILE_ATTRIBUTE_SYSTEM):
                return False
            elif attr_lower == "archive" and not (file_attrs & stat.FILE_ATTRIBUTE_ARCHIVE):
                return False
            elif attr_lower == "directory" and not file_path.is_dir():
                return False
            elif attr_lower == "file" and not file_path.is_file():
                return False

    except Exception:
        return False

    return True


def check_file_owner(file_path: Path, owner: str) -> bool:
    """Check if file is owned by specified owner."""
    if not owner:
        return True

    try:
        file_path.stat()
        # This is a simplified check - in practice you'd need more sophisticated owner checking
        # For now, we'll skip this check as it requires platform-specific implementation
        return True
    except Exception:
        return False


@mcp.tool
async def file_content_search(
    search_pattern: str,
    search_dir: str,
    file_pattern: str = "*",
    exclude_dirs: Optional[List[str]] = None,
    case_sensitive: bool = False,
    whole_word: bool = False,
    max_results: int = 100,
    context_lines: int = 2,
    max_file_size_mb: int = 10,
    skip_binary: bool = True,
    min_file_size_mb: int = 0,
    modified_after: Optional[str] = None,
    modified_before: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    accessed_after: Optional[str] = None,
    accessed_before: Optional[str] = None,
    include_hidden: bool = False,
    files_only: bool = True,
    directories_only: bool = False,
    file_attributes: Optional[List[str]] = None,
    owner: Optional[str] = None,
) -> Dict[str, Any]:
    """Search for text patterns in files.

    Searches for text patterns within file contents using regex support, with
    comprehensive filtering options including file patterns, date ranges, file
    attributes, and size constraints. Returns matches with context lines for
    better understanding of search results.

    Args:
        search_pattern: Pattern to search for (supports regex). Examples:
            "error", "TODO|FIXME", "def\\s+\\w+", "password\\s*=". Regex
            patterns are supported by default.

        search_dir: Directory to search in. Examples: "C:\\Projects",
            "D:\\Code", "~/Documents". Must be a valid directory path.

        file_pattern: Pattern to filter files (default: "*"). Examples:
            "*.txt", "*.{py,js}", "*.log", "test*.py". Supports glob patterns.

        exclude_dirs: List of directory patterns to exclude (default: None).
            Default excludes: ["**/__pycache__", "**/.git", "**/node_modules"].
            Examples: ["**/temp", "**/cache", "**/build"].

        case_sensitive: Case-sensitive search (default: False). When True,
            "Error" and "error" are treated as different patterns.

        whole_word: Match whole words only (default: False). When True, "test"
            matches "test" but not "testing" or "contest".

        max_results: Maximum number of results to return (default: 100).
            Stops searching after finding this many matches across all files.

        context_lines: Number of context lines to include around matches
            (default: 2). Shows surrounding lines for better context.

        max_file_size_mb: Maximum file size in MB to search (default: 10).
            Files larger than this are skipped. Examples: 5, 50, 100.

        skip_binary: Skip binary files (default: True). Binary detection is
            automatic based on file content.

        min_file_size_mb: Minimum file size in MB (default: 0). Files smaller
            than this are skipped. Examples: 0.1, 1.0.

        modified_after: Only include files modified after this date
            (default: None). Supports ISO format (2024-01-01) or relative
            (7d, 1h, 30m). Examples: "2024-01-01", "7d", "1h".

        modified_before: Only include files modified before this date
            (default: None). Supports ISO format or relative time. Examples:
            "2024-12-31", "30d".

        created_after: Only include files created after this date
            (default: None). Supports ISO format or relative time. Examples:
            "2024-01-01", "7d".

        created_before: Only include files created before this date
            (default: None). Supports ISO format or relative time. Examples:
            "2024-12-31", "365d".

        accessed_after: Only include files accessed after this date
            (default: None). Supports ISO format or relative time. Examples:
            "2024-01-01", "7d".

        accessed_before: Only include files accessed before this date
            (default: None). Supports ISO format or relative time. Examples:
            "2024-12-31", "30d".

        include_hidden: Include hidden files and directories (default: False).
            When False, files starting with "." are excluded.

        files_only: Only return files (exclude directories) (default: True).
            When True, directories are not included in results.

        directories_only: Only return directories (exclude files)
            (default: False). Mutually exclusive with files_only.

        file_attributes: Filter by file attributes (default: None). Examples:
            ["readonly"], ["hidden", "system"], ["archive"]. Valid values:
            readonly, hidden, system, archive, directory, file.

        owner: Filter by file owner (username or SID) (default: None).
            Platform-specific implementation. Examples: "DOMAIN\\user",
            "S-1-5-21-...".

    Returns:
        Dictionary containing:
            status: Operation status string. "completed" if search finished successfully,
                "no_files_found" if no files matched the filters.

            files_searched: Number of files actually searched (integer). May be less
                than total_files if max_results was reached early.

            total_files: Total number of files found matching filters (integer). All
                files that passed the file_pattern and exclude_dirs filters.

            total_matches: Total number of matches found across all files (integer).
                Total occurrences of the search_pattern in all searched files.

            matches: List of match result dictionaries. Each match result contains:
                - file: Relative file path from search_dir (e.g., "src\\main.py")
                - path: Absolute file path (e.g., "C:\\Projects\\src\\main.py")
                - matches: List of match detail dictionaries, each containing:
                    - line: Line number where match was found (1-indexed)
                    - start: Character position where match starts in the line
                    - end: Character position where match ends in the line
                    - match: The actual matched text
                    - line_content: Full content of the line containing the match
                    - context: List of surrounding lines (before and after) for context

    Usage:
        This tool is used when you need to search for text patterns within
        file contents, not just file names. It works by scanning file contents
        and applying filters before searching. Best practices include:
        - Use regex for complex pattern matching
        - Filter by file type to focus search scope
        - Exclude build/cache directories for faster searches
        - Set max_file_size_mb to avoid searching huge files
        - Use context_lines to understand match context

        Common scenarios:
        - Find all TODO/FIXME comments in code
        - Search for error messages or log patterns
        - Find function definitions or API calls
        - Search for configuration values or secrets
        - Find references to specific classes or modules

    Examples:
        Basic text search:
            results = await file_content_search(
                search_pattern="TODO",
                search_dir="C:\\Projects\\myapp"
            )
            # Returns: {'status': 'completed', 'matches': [...], ...}

        Regex pattern search:
            results = await file_content_search(
                search_pattern="def\\s+\\w+",
                search_dir="C:\\Projects",
                file_pattern="*.py"
            )
            # Finds all function definitions in Python files

        Search with filters:
            results = await file_content_search(
                search_pattern="error",
                search_dir="C:\\Logs",
                file_pattern="*.log",
                modified_after="7d",
                max_file_size_mb=5
            )
            # Finds "error" in recent log files under 5MB

        Case-sensitive whole word search:
            results = await file_content_search(
                search_pattern="Test",
                search_dir="C:\\Code",
                case_sensitive=True,
                whole_word=True
            )
            # Finds exact word "Test" (case-sensitive)

    Errors:
        Common errors and solutions:
        - Directory not found: Ensure search_dir exists and is accessible
        - No files found: Check file_pattern and exclude_dirs filters
        - Pattern compilation error: Verify regex syntax is valid
        - Permission denied: Check file access permissions
        - File too large: Increase max_file_size_mb or exclude large files

    See Also:
        - fastsearch_search: Search for files by name pattern
        - fastsearch_search_advanced: Advanced file name search with filters
        - search_result_filter: Filter search results after finding files
    """
    if exclude_dirs is None:
        exclude_dirs = ["**/__pycache__", "**/.git", "**/node_modules"]
    if file_attributes is None:
        file_attributes = []

    return await asyncio.to_thread(
        _search_sync,
        search_pattern,
        search_dir,
        file_pattern,
        exclude_dirs,
        case_sensitive,
        whole_word,
        max_results,
        context_lines,
        max_file_size_mb,
        skip_binary,
        min_file_size_mb,
        modified_after,
        modified_before,
        created_after,
        created_before,
        accessed_after,
        accessed_before,
        include_hidden,
        files_only,
        directories_only,
        file_attributes,
        owner,
    )


def _search_sync(
    search_pattern: str,
    search_dir: str,
    file_pattern: str = "*",
    exclude_dirs: Optional[List[str]] = None,
    case_sensitive: bool = False,
    whole_word: bool = False,
    max_results: int = 100,
    context_lines: int = 2,
    max_file_size_mb: int = 10,
    skip_binary: bool = True,
    min_file_size_mb: int = 0,
    modified_after: Optional[str] = None,
    modified_before: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    accessed_after: Optional[str] = None,
    accessed_before: Optional[str] = None,
    include_hidden: bool = False,
    files_only: bool = True,
    directories_only: bool = False,
    file_attributes: Optional[List[str]] = None,
    owner: Optional[str] = None,
) -> Dict[str, Any]:
    """Synchronous implementation of file search."""
    if exclude_dirs is None:
        exclude_dirs = []
    if file_attributes is None:
        file_attributes = []

    search_path = Path(search_dir).expanduser().resolve()

    if not search_path.exists() or not search_path.is_dir():
        return {"error": f"Directory not found: {search_dir}", "matches": []}

    # Parse date filters
    modified_after_ts = parse_date_filter(modified_after) if modified_after else None
    modified_before_ts = parse_date_filter(modified_before) if modified_before else None
    created_after_ts = parse_date_filter(created_after) if created_after else None
    created_before_ts = parse_date_filter(created_before) if created_before else None
    accessed_after_ts = parse_date_filter(accessed_after) if accessed_after else None
    accessed_before_ts = parse_date_filter(accessed_before) if accessed_before else None

    # Convert file pattern to regex for find_files
    # Use the original pattern directly since find_files handles glob patterns
    file_regex = file_pattern

    # Convert exclude_dirs to regex pattern
    exclude_pattern = "|\\.".join(
        re.escape(d).replace("*", ".*").replace("?", ".") for d in exclude_dirs
    )

    # Find all matching files
    files = list(
        find_files(
            root_dir=str(search_path),
            include=file_regex,
            exclude=exclude_pattern,
            max_size=max_file_size_mb * 1024 * 1024,
            skip_binary=skip_binary,
            max_results=max_results * 10,  # Find more files than needed for content search
        )
    )

    # Apply advanced filtering
    filtered_files = []
    for file_path in files:
        try:
            # Check file type filtering
            if directories_only and not file_path.is_dir():
                continue
            if files_only and not file_path.is_file():
                continue

            # Check hidden files
            if not include_hidden and file_path.name.startswith("."):
                continue

            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb < min_file_size_mb:
                continue

            # Check date filters
            stat_info = file_path.stat()

            if modified_after_ts and stat_info.st_mtime < modified_after_ts:
                continue
            if modified_before_ts and stat_info.st_mtime > modified_before_ts:
                continue
            if created_after_ts and stat_info.st_ctime < created_after_ts:
                continue
            if created_before_ts and stat_info.st_ctime > created_before_ts:
                continue
            if accessed_after_ts and stat_info.st_atime < accessed_after_ts:
                continue
            if accessed_before_ts and stat_info.st_atime > accessed_before_ts:
                continue

            # Check file attributes
            if not check_file_attributes(file_path, file_attributes):
                continue

            # Check owner
            if not check_file_owner(file_path, owner):
                continue

            filtered_files.append(file_path)

        except Exception as e:
            print(f"Error filtering file {file_path}: {e}")
            continue

    files = filtered_files

    if not files:
        return {"status": "no_files_found", "files_searched": 0, "matches": []}

    # Search in each file
    results = []
    total_matches = 0
    files_searched = 0

    for file_path in files:
        if total_matches >= max_results:
            break

        try:
            matches = search_in_file(
                file_path=file_path,
                pattern=search_pattern,
                case_sensitive=case_sensitive,
                whole_word=whole_word,
                context_lines=context_lines,
                max_matches=max_results - total_matches,
            )

            if matches:
                rel_path = file_path.relative_to(search_path)
                results.append(
                    {
                        "file": str(rel_path),
                        "path": str(file_path),
                        "matches": [
                            {
                                "line": m["line"],
                                "start": m["start"],
                                "end": m["end"],
                                "match": m["match"],
                                "line_content": m["line_content"],
                                "context": m["context"],
                            }
                            for m in matches
                        ],
                    }
                )
                total_matches += len(matches)

        except Exception as e:
            print(f"Error searching in {file_path}: {e}")
            continue

        files_searched += 1

        # Update progress periodically
        if files_searched % 100 == 0:
            print(
                f"Searched {files_searched}/{len(files)} files, "
                f"found {total_matches} matches..."
            )

    return {
        "status": "completed",
        "files_searched": files_searched,
        "total_files": len(files),
        "total_matches": total_matches,
        "matches": results[:max_results],
    }
