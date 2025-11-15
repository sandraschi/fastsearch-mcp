"""File content search tool for MCP."""

import asyncio
import re
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastsearch_mcp.tools.base import BaseTool, ToolCategory, ToolParameter, tool
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


@tool(
    name="file_content_search",
    description="Search for text patterns in files",
    category=ToolCategory.FILESYSTEM,
    parameters=[
        ToolParameter(
            name="search_pattern",
            type=str,
            description="Pattern to search for (supports regex)",
            required=True,
        ),
        ToolParameter(
            name="search_dir", type=str, description="Directory to search in", required=True
        ),
        ToolParameter(
            name="file_pattern",
            type=str,
            description="Pattern to filter files (e.g., '*.txt' or '*.{py,js}')",
            default="*",
        ),
        ToolParameter(
            name="exclude_dirs",
            type=list,
            description="List of directory patterns to exclude",
            default=["**/__pycache__", "**/.git", "**/node_modules"],
        ),
        ToolParameter(
            name="case_sensitive", type=bool, description="Case-sensitive search", default=False
        ),
        ToolParameter(
            name="whole_word", type=bool, description="Match whole words only", default=False
        ),
        ToolParameter(
            name="max_results",
            type=int,
            description="Maximum number of results to return",
            default=100,
        ),
        ToolParameter(
            name="context_lines",
            type=int,
            description="Number of context lines to include around matches",
            default=2,
        ),
        ToolParameter(
            name="max_file_size_mb",
            type=int,
            description="Maximum file size in MB to search",
            default=10,
        ),
        ToolParameter(name="skip_binary", type=bool, description="Skip binary files", default=True),
        # Advanced filtering parameters
        ToolParameter(
            name="min_file_size_mb",
            type=int,
            description="Minimum file size in MB",
            default=0,
            min=0,
        ),
        ToolParameter(
            name="modified_after",
            type=str,
            description=(
                "Only include files modified after this date "
                "(YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
            ),
            required=False,
        ),
        ToolParameter(
            name="modified_before",
            type=str,
            description=(
                "Only include files modified before this date "
                "(YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
            ),
            required=False,
        ),
        ToolParameter(
            name="created_after",
            type=str,
            description="Only include files created after this date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
            required=False,
        ),
        ToolParameter(
            name="created_before",
            type=str,
            description="Only include files created before this date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
            required=False,
        ),
        ToolParameter(
            name="accessed_after",
            type=str,
            description="Only include files accessed after this date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
            required=False,
        ),
        ToolParameter(
            name="accessed_before",
            type=str,
            description="Only include files accessed before this date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
            required=False,
        ),
        ToolParameter(
            name="include_hidden",
            type=bool,
            description="Include hidden files and directories",
            default=False,
        ),
        ToolParameter(
            name="files_only",
            type=bool,
            description="Only return files (exclude directories)",
            default=True,
        ),
        ToolParameter(
            name="directories_only",
            type=bool,
            description="Only return directories (exclude files)",
            default=False,
        ),
        ToolParameter(
            name="file_attributes",
            type=list,
            description="Filter by file attributes (readonly, system, archive, hidden, etc.)",
            required=False,
        ),
        ToolParameter(
            name="owner",
            type=str,
            description="Filter by file owner (username or SID)",
            required=False,
        ),
    ],
    return_type=Dict[str, Any],
    return_description="Search results with file paths and matches",
)
class FileContentSearchTool(BaseTool):
    """Tool for searching text patterns in files."""

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the file content search."""
        # Extract the parameters we need
        search_pattern = kwargs.get("search_pattern", "")
        search_dir = kwargs.get("search_dir", ".")
        file_pattern = kwargs.get("file_pattern", "*")
        exclude_dirs = kwargs.get("exclude_dirs", [])
        case_sensitive = kwargs.get("case_sensitive", False)
        whole_word = kwargs.get("whole_word", False)
        max_results = kwargs.get("max_results", 100)
        context_lines = kwargs.get("context_lines", 2)
        max_file_size_mb = kwargs.get("max_file_size_mb", 10)
        skip_binary = kwargs.get("skip_binary", True)

        # Advanced filtering parameters
        min_file_size_mb = kwargs.get("min_file_size_mb", 0)
        modified_after = kwargs.get("modified_after")
        modified_before = kwargs.get("modified_before")
        created_after = kwargs.get("created_after")
        created_before = kwargs.get("created_before")
        accessed_after = kwargs.get("accessed_after")
        accessed_before = kwargs.get("accessed_before")
        include_hidden = kwargs.get("include_hidden", False)
        files_only = kwargs.get("files_only", True)
        directories_only = kwargs.get("directories_only", False)
        file_attributes = kwargs.get("file_attributes", [])
        owner = kwargs.get("owner")

        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._search_sync,
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
        self,
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
        **kwargs,
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
                    f"Searched {files_searched}/{len(files)} files, found {total_matches} matches..."
                )

        return {
            "status": "completed",
            "files_searched": files_searched,
            "total_files": len(files),
            "total_matches": total_matches,
            "matches": results[:max_results],
        }
