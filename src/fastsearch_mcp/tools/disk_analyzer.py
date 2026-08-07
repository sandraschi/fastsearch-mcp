"""Disk space analyzer tool for MCP."""

import asyncio
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from fastsearch_mcp.logging_config import get_logger
from fastsearch_mcp.mcp_instance import mcp

logger = get_logger(__name__)


@dataclass
class DiskUsage:
    """Disk usage information for a directory."""

    path: str
    size: int  # in bytes
    file_count: int = 0
    dir_count: int = 0
    children: list["DiskUsage"] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to a dictionary for JSON serialization."""
        return {
            "path": self.path,
            "size": self.size,
            "size_human": self.human_size(),
            "file_count": self.file_count,
            "dir_count": self.dir_count,
            "children": [child.to_dict() for child in self.children],
        }

    def human_size(self, decimal_places: int = 2) -> str:
        """Return a human-readable size string."""
        size = self.size
        units = ["B", "KB", "MB", "GB", "TB"]
        for unit_index, _unit in enumerate(units):
            if size < 1024.0:
                return f"{size:.{decimal_places}f} {units[unit_index]}"
            size /= 1024.0
        return f"{size:.{decimal_places}f} {units[-1]}"


def get_disk_usage(path: str | Path, max_depth: int = 3, max_entries: int = 10000) -> DiskUsage:
    """Get disk usage information for a directory with limits to prevent hangs."""
    path = Path(path).resolve()
    usage = DiskUsage(path=str(path), size=0)
    entries_processed = 0

    def scan_dir(current_path: Path, depth: int, max_d: int) -> DiskUsage:
        nonlocal entries_processed
        current_usage = DiskUsage(path=str(current_path), size=0)

        if entries_processed >= max_entries or depth > max_d:
            return current_usage

        try:
            for entry in os.scandir(current_path):
                if entries_processed >= max_entries:
                    break

                try:
                    if entry.is_symlink():
                        continue

                    if entry.is_file():
                        current_usage.file_count += 1
                        current_usage.size += entry.stat().st_size
                        entries_processed += 1

                    elif entry.is_dir():
                        if depth < max_d:
                            child_usage = scan_dir(entry.path, depth + 1, max_d)
                            current_usage.dir_count += 1 + child_usage.dir_count
                            current_usage.file_count += child_usage.file_count
                            current_usage.size += child_usage.size
                            if len(current_usage.children) < 20:  # Limit children to prevent huge responses
                                current_usage.children.append(child_usage)
                        else:
                            current_usage.dir_count += 1
                            # Estimate size using shutil.disk_usage for performance
                            try:
                                du = shutil.disk_usage(entry.path)
                                current_usage.size += du.used
                            except (OSError, PermissionError):
                                pass
                        entries_processed += 1

                except (PermissionError, OSError) as e:
                    logger.debug("Error accessing %s: %s", entry.path, e)
                    continue

        except (PermissionError, OSError) as e:
            logger.warning("Error scanning directory %s: %s", current_path, e)

        return current_usage

    usage = scan_dir(path, 0, max_depth)
    usage.path = str(path)
    return usage


def get_largest_files(path: str | Path, limit: int = 50, max_files_to_scan: int = 10000) -> list[dict]:
    """Get the largest files in a directory with early termination."""
    path = Path(path).resolve()
    largest = []
    files_scanned = 0

    def scan_dir(directory: Path, depth: int = 0, max_depth: int = 5):
        nonlocal files_scanned
        if depth > max_depth or files_scanned >= max_files_to_scan:
            return

        try:
            for entry in directory.iterdir():
                if files_scanned >= max_files_to_scan:
                    break

                try:
                    if entry.is_symlink():
                        continue

                    if entry.is_file():
                        stat = entry.stat()
                        largest.append((entry, stat.st_size))
                        files_scanned += 1
                        # Keep only the largest files
                        largest.sort(key=lambda x: x[1], reverse=True)
                        if len(largest) > limit * 2:  # Keep some extra to avoid frequent resizing
                            largest.pop()

                    elif entry.is_dir() and depth < max_depth:
                        scan_dir(entry, depth + 1, max_depth)

                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError):
            pass

    try:
        scan_dir(path)
    except Exception as e:
        logger.warning("Error finding largest files in %s: %s", path, e)

    return [
        {
            "path": str(file.relative_to(path)),
            "size": size,
            "size_human": f"{size / (1024 * 1024):.2f} MB",
        }
        for file, size in largest[:limit]
    ]


def get_disk_partitions() -> list[dict]:
    """Get information about all disk partitions."""
    partitions = []

    try:
        import psutil

        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append(
                    {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "opts": partition.opts,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                    }
                )
            except Exception as e:
                logger.warning("Error getting usage for %s: %s", partition.mountpoint, e)
    except ImportError:
        logger.warning("psutil not available, using basic disk info")

    return partitions


@mcp.tool
async def analyze_disk_usage(
    path: str = "C:\\",
    max_depth: int = 3,
    include_partitions: bool = True,
    find_large_files: bool = True,
    large_file_limit: int = 50,
    min_file_size_mb: int = 10,
) -> dict:
    """Analyze disk usage and find large files and directories.

    Provides comprehensive disk usage analysis including partition information,
    directory sizes, and identification of large files.

    Args:
        path: Path to analyze (default: C:\\) or root of all mounted filesystems
        max_depth: Maximum depth to analyze (0 for unlimited)
        include_partitions: Include disk partition information
        find_large_files: Find largest files in the directory
        large_file_limit: Number of largest files to find
        min_file_size_mb: Minimum file size to consider (in MB)

    Returns:
        Disk usage analysis results
    """
    return await asyncio.to_thread(
        _analyze_disk_usage_sync,
        path,
        max_depth,
        include_partitions,
        find_large_files,
        large_file_limit,
        min_file_size_mb,
    )


def _analyze_disk_usage_sync(
    path: str = "C:\\",
    max_depth: int = 3,
    include_partitions: bool = True,
    find_large_files: bool = True,
    large_file_limit: int = 50,
    min_file_size_mb: int = 10,
) -> dict:
    """Synchronous implementation of disk analysis."""
    result = {"path": path, "status": "completed"}

    # Get partition information
    if include_partitions:
        try:
            result["partitions"] = get_disk_partitions()
        except Exception as e:
            logger.error("Error getting partition info: %s", e)
            result["partitions"] = []

    # Analyze disk usage
    try:
        # Limit entries to prevent hangs on large directories
        max_entries = 5000 if max_depth > 2 else 10000
        usage = get_disk_usage(path, max_depth, max_entries=max_entries)
        result["disk_usage"] = usage.to_dict()
    except Exception as e:
        logger.error("Error analyzing disk usage: %s", e)
        result["error"] = f"Failed to analyze disk usage: {e}"

    # Find large files
    if find_large_files:
        try:
            min_size = min_file_size_mb * 1024 * 1024
            # Limit scanning to prevent hangs
            large_files = get_largest_files(path, large_file_limit, max_files_to_scan=5000)
            result["large_files"] = [f for f in large_files if f["size"] >= min_size][:large_file_limit]
        except Exception as e:
            logger.error("Error finding large files: %s", e)
            result["error"] = f"Failed to find large files: {e}"

    return result
