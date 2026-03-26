"""
File utilities for FastSearch MCP.

This module provides file system utilities following FastMCP 2.13 patterns.
"""

import logging
import os
import re
from pathlib import Path
from typing import Iterator, List, Optional, Pattern

logger = logging.getLogger(__name__)


def find_files(
    root_dir: str,
    include: str = "*",
    exclude: Optional[str] = None,
    max_size: Optional[int] = None,
    skip_binary: bool = True,
    max_results: int = 100,
) -> Iterator[Path]:
    """
    Find files matching patterns using directory tree walk (fallback implementation).

    Args:
        root_dir: Root directory to search in
        include: Include pattern (glob)
        exclude: Exclude pattern (glob)
        max_size: Maximum file size in bytes
        skip_binary: Whether to skip binary files
        max_results: Maximum number of results to return

    Returns:
        Iterator of matching file paths
    """
    root_path = Path(root_dir)
    if not root_path.exists():
        return

    # Convert glob patterns to regex
    include_regex = _glob_to_regex(include)
    exclude_regex = _glob_to_regex(exclude) if exclude else None

    count = 0
    try:
        # Use os.walk for directory traversal (fallback implementation)
        for root, dirs, files in os.walk(root_path):
            # Skip excluded directories
            if exclude_regex:
                dirs[:] = [d for d in dirs if not exclude_regex.search(d)]

            for file in files:
                if count >= max_results:
                    return

                file_path = Path(root) / file

                # Check file size limit
                if max_size:
                    try:
                        if file_path.stat().st_size > max_size:
                            continue
                    except OSError:
                        continue

                # Check if file matches include pattern
                if include_regex.search(file_path.name):
                    # Skip binary files if requested
                    if skip_binary and is_binary_file(str(file_path)):
                        continue

                    yield file_path
                    count += 1

    except Exception as e:
        logger.error(f"Error searching files: {e}")


def search_in_file(
    file_path: str,
    pattern: str,
    case_sensitive: bool = False,
    whole_word: bool = False,
    context_lines: int = 0,
    max_matches: int = 100,
) -> List[dict]:
    """
    Search for a pattern within a file.

    Args:
        file_path: Path to the file to search
        pattern: Pattern to search for
        case_sensitive: Whether the search should be case sensitive
        whole_word: Whether to match whole words only
        context_lines: Number of context lines to include around matches
        max_matches: Maximum number of matches to return

    Returns:
        List of matches with line numbers and content
    """
    matches = []

    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                if len(matches) >= max_matches:
                    break

                # Prepare the search text
                search_text = line
                search_pattern = pattern

                if not case_sensitive:
                    search_text = search_text.lower()
                    search_pattern = search_pattern.lower()

                # Check for matches
                if whole_word:
                    # Use word boundaries for whole word matching
                    import re

                    word_pattern = r"\b" + re.escape(search_pattern) + r"\b"
                    if re.search(word_pattern, search_text):
                        match_found = True
                    else:
                        match_found = False
                else:
                    match_found = search_pattern in search_text

                if match_found:
                    # Find the position of the match
                    start_pos = search_text.find(search_pattern)
                    end_pos = start_pos + len(search_pattern)

                    # Get context lines
                    context = []
                    if context_lines > 0:
                        start_line = max(1, line_num - context_lines)
                        end_line = min(len(lines), line_num + context_lines)
                        for i in range(start_line - 1, end_line):
                            context.append({"line": i + 1, "content": lines[i].rstrip()})

                    matches.append(
                        {
                            "line": line_num,
                            "start": start_pos,
                            "end": end_pos,
                            "match": pattern,
                            "line_content": line.rstrip(),
                            "context": context,
                        }
                    )

    except Exception as e:
        logger.error(f"Error searching in file {file_path}: {e}")

    return matches


def _glob_to_regex(glob_pattern: str) -> Pattern[str]:
    """Convert glob pattern to regex pattern."""
    # Simple glob to regex conversion
    regex_pattern = glob_pattern.replace(".", r"\.")
    regex_pattern = regex_pattern.replace("*", ".*")
    regex_pattern = regex_pattern.replace("?", ".")
    regex_pattern = f"^{regex_pattern}$"

    return re.compile(regex_pattern)


def is_binary_file(file_path: str) -> bool:
    """
    Check if a file is binary.

    Args:
        file_path: Path to the file

    Returns:
        True if the file is binary, False otherwise
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\0" in chunk
    except Exception:
        return False


def get_file_info(file_path: str) -> dict:
    """
    Get information about a file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with file information
    """
    try:
        path = Path(file_path)
        stat = path.stat()

        return {
            "path": str(path),
            "name": path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "exists": path.exists(),
        }
    except Exception as e:
        return {"path": file_path, "error": str(e), "exists": False}
