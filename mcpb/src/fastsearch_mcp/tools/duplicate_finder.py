"""Duplicate file finder tool for MCP."""

import asyncio
import hashlib
import os
from collections import defaultdict
from pathlib import Path

from fastsearch_mcp.logging_config import get_logger
from fastsearch_mcp.mcp_instance import mcp
from fastsearch_mcp.utils.file_utils import find_files

logger = get_logger(__name__)

# Chunk size for reading files (1MB)
CHUNK_SIZE = 1024 * 1024


def get_file_hash(file_path: Path, fast_check: bool = False) -> str | None:
    """Calculate the hash of a file's content.

    Args:
        file_path: Path to the file
        fast_check: If True, only hash the first and last 64KB of the file for speed

    Returns:
        str: Hex digest of the file's hash, or None if the file couldn't be read
    """
    try:
        file_size = file_path.stat().st_size

        # For empty files, return a constant hash
        if file_size == 0:
            return hashlib.md5().hexdigest()

        # For small files, just hash the whole thing
        if file_size <= 2 * CHUNK_SIZE or not fast_check:
            hasher = hashlib.md5()
            with open(file_path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    hasher.update(chunk)
            return hasher.hexdigest()

        # For large files, hash the first and last chunks to speed things up
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            # Hash the first chunk
            hasher.update(f.read(CHUNK_SIZE))

            # If the file is larger than 2 chunks, seek to near the end and hash the last chunk
            if file_size > 2 * CHUNK_SIZE:
                f.seek(-CHUNK_SIZE, 2)  # Seek to CHUNK_SIZE bytes from the end
                hasher.update(f.read())

        return hasher.hexdigest()

    except OSError as e:
        logger.debug("Error hashing file %s: %s", file_path, e)
        return None


def _find_duplicate_files_impl(
    search_dir: str,
    min_size: int = 0,
    max_size: int | None = None,
    file_pattern: str = "*",
    exclude_dirs: list[str] | None = None,
    fast_mode: bool = True,
    compare_content: bool = True,
) -> dict[str, list[str]]:
    """Find duplicate files in a directory.

    Args:
        search_dir: Directory to search in
        min_size: Minimum file size in bytes
        max_size: Maximum file size in bytes
        file_pattern: File pattern to match (e.g., '*.jpg')
        exclude_dirs: List of directory patterns to exclude
        fast_mode: If True, use faster but less accurate hashing
        compare_content: If True, compare file contents for potential duplicates

    Returns:
        Dict mapping file hashes to lists of duplicate file paths
    """
    if exclude_dirs is None:
        exclude_dirs = []

    # First, find all files and group them by size (files with same size could be duplicates)
    size_map = defaultdict(list)

    for file_path in find_files(
        search_dir,
        include=file_pattern,
        exclude="|".join(exclude_dirs) if exclude_dirs else None,
        min_size=min_size,
        max_size=max_size,
        skip_binary=True,
    ):
        try:
            file_size = file_path.stat().st_size
            size_map[file_size].append(file_path)
        except OSError as e:
            logger.debug("Error getting size for %s: %s", file_path, e)

    # For files with unique sizes, they can't have duplicates
    potential_duplicates = {size: paths for size, paths in size_map.items() if len(paths) > 1}

    if not potential_duplicates or not compare_content:
        # If we're not comparing content, return files with the same size as potential duplicates
        return {f"size_{size}": [str(p) for p in paths] for size, paths in potential_duplicates.items()}

    # Now, for files with the same size, compare their content hashes
    hash_map = defaultdict(list)

    for _size, file_paths in potential_duplicates.items():
        if len(file_paths) < 2:
            continue

        # For each potential duplicate, calculate its hash
        for file_path in file_paths:
            file_hash = get_file_hash(file_path, fast_mode)
            if file_hash is not None:
                hash_map[file_hash].append(file_path)

    # Filter out hashes with only one file (no duplicates)
    return {hash_val: [str(p) for p in paths] for hash_val, paths in hash_map.items() if len(paths) > 1}


@mcp.tool
async def find_duplicate_files(
    search_dir: str,
    min_size: int = 1024,
    max_size: int | None = None,
    file_pattern: str = "*",
    exclude_dirs: list[str] | None = None,
    fast_mode: bool = True,
    compare_content: bool = True,
    min_duplicate_group: int = 2,
    max_results: int = 100,
) -> dict:
    """Find duplicate files based on content hashing.

    Searches for duplicate files by comparing file sizes and content hashes.
    Can use fast mode for quicker results or full content comparison for accuracy.

    Args:
        search_dir: Directory to search for duplicates
        min_size: Minimum file size in bytes to consider
        max_size: Maximum file size in bytes to consider
        file_pattern: File pattern to match (e.g., '*.jpg' or '*.{jpg,png}')
        exclude_dirs: List of directory patterns to exclude from search
        fast_mode: Use faster but less accurate hashing (checks only start/end of files)
        compare_content: Compare file contents (slower but more accurate)
        min_duplicate_group: Minimum number of duplicates to report
        max_results: Maximum number of duplicate groups to return

    Returns:
        Dictionary with hash as key and list of duplicate file paths as value
    """
    if exclude_dirs is None:
        exclude_dirs = ["**/__pycache__", "**/.git", "**/node_modules"]

    return await asyncio.to_thread(
        _find_duplicates_sync,
        search_dir,
        min_size,
        max_size,
        file_pattern,
        exclude_dirs,
        fast_mode,
        compare_content,
        min_duplicate_group,
        max_results,
    )


def _find_duplicates_sync(
    search_dir: str,
    min_size: int = 1024,
    max_size: int | None = None,
    file_pattern: str = "*",
    exclude_dirs: list[str] | None = None,
    fast_mode: bool = True,
    compare_content: bool = True,
    min_duplicate_group: int = 2,
    max_results: int = 100,
) -> dict:
    """Synchronous implementation of duplicate file search."""
    if exclude_dirs is None:
        exclude_dirs = []

    result = {
        "search_dir": search_dir,
        "total_files_processed": 0,
        "duplicate_groups": 0,
        "duplicate_files": 0,
        "duplicates": {},
    }

    try:
        # Find all duplicate files
        duplicates = _find_duplicate_files_impl(
            search_dir=search_dir,
            min_size=min_size,
            max_size=max_size,
            file_pattern=file_pattern,
            exclude_dirs=exclude_dirs,
            fast_mode=fast_mode,
            compare_content=compare_content,
        )

        # Sort by number of duplicates (descending) and limit results
        sorted_duplicates = sorted(
            duplicates.items(),
            key=lambda x: (
                len(x[1]),
                sum(os.path.getsize(f) for f in x[1] if os.path.exists(f)),
            ),
            reverse=True,
        )

        # Filter and format results
        duplicate_count = 0
        for hash_val, files in sorted_duplicates:
            if len(files) < min_duplicate_group:
                continue

            # Get file sizes and calculate total wasted space
            files_with_size = []
            total_size = 0

            for file_path in files:
                try:
                    file_size = os.path.getsize(file_path)
                    files_with_size.append(
                        {
                            "path": file_path,
                            "size": file_size,
                            "size_human": f"{file_size / (1024 * 1024):.2f} MB",
                        }
                    )
                    total_size += file_size
                except OSError:
                    continue

            if len(files_with_size) < min_duplicate_group:
                continue

            # Add to results
            result["duplicates"][hash_val] = {
                "file_count": len(files_with_size),
                "total_size": total_size,
                "total_size_human": f"{total_size / (1024 * 1024):.2f} MB",
                "wasted_space": total_size - (total_size // len(files_with_size)),
                "files": files_with_size,
            }

            duplicate_count += 1
            if duplicate_count >= max_results:
                break

        # Update summary
        result["duplicate_groups"] = len(result["duplicates"])
        result["duplicate_files"] = sum(len(group["files"]) for group in result["duplicates"].values())
        result["total_wasted"] = sum(group["wasted_space"] for group in result["duplicates"].values())
        result["total_wasted_human"] = f"{result['total_wasted'] / (1024 * 1024):.2f} MB"

    except Exception as e:
        logger.exception("Error finding duplicate files")
        result["error"] = str(e)

    return result
