"""Disk space analyzer tool for MCP."""
import asyncio
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from fastsearch_mcp.tools.base import BaseTool, ToolCategory, ToolParameter, tool
from fastsearch_mcp.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class DiskUsage:
    """Disk usage information for a directory."""
    path: str
    size: int  # in bytes
    file_count: int = 0
    dir_count: int = 0
    children: List['DiskUsage'] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to a dictionary for JSON serialization."""
        return {
            'path': self.path,
            'size': self.size,
            'size_human': self.human_size(),
            'file_count': self.file_count,
            'dir_count': self.dir_count,
            'children': [child.to_dict() for child in self.children]
        }
    
    def human_size(self, decimal_places: int = 2) -> str:
        """Return a human-readable size string."""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                break
            size /= 1024.0
        return f"{size:.{decimal_places}f} {unit}"


def get_disk_usage(path: Union[str, Path], max_depth: int = 3) -> DiskUsage:
    """Get disk usage information for a directory."""
    path = Path(path).resolve()
    usage = DiskUsage(path=str(path), size=0)
    
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_symlink():
                    continue
                    
                if entry.is_file():
                    usage.file_count += 1
                    usage.size += entry.stat().st_size
                    
                elif entry.is_dir():
                    if max_depth > 0:
                        child_usage = get_disk_usage(entry.path, max_depth - 1)
                        usage.dir_count += 1 + child_usage.dir_count
                        usage.file_count += child_usage.file_count
                        usage.size += child_usage.size
                        usage.children.append(child_usage)
                    else:
                        # Just count the directory without recursing
                        usage.dir_count += 1
                        # Estimate size using shutil.disk_usage for performance
                        try:
                            du = shutil.disk_usage(entry.path)
                            usage.size += du.used
                        except (OSError, PermissionError):
                            pass
                            
            except (PermissionError, OSError) as e:
                logger.debug("Error accessing %s: %s", entry.path, e)
                continue
                
    except (PermissionError, OSError) as e:
        logger.warning("Error scanning directory %s: %s", path, e)
        
    return usage


def get_largest_files(path: Union[str, Path], limit: int = 50) -> List[Dict]:
    """Get the largest files in a directory."""
    path = Path(path).resolve()
    largest = []
    
    def scan_dir(directory: Path):
        try:
            for entry in directory.iterdir():
                try:
                    if entry.is_symlink():
                        continue
                        
                    if entry.is_file():
                        stat = entry.stat()
                        largest.append((entry, stat.st_size))
                        # Keep only the largest files
                        largest.sort(key=lambda x: x[1], reverse=True)
                        if len(largest) > limit * 2:  # Keep some extra to avoid frequent resizing
                            largest.pop()
                            
                    elif entry.is_dir():
                        scan_dir(entry)
                        
                except (PermissionError, OSError):
                    continue
                    
        except (PermissionError, OSError):
            pass
    
    try:
        scan_dir(path)
    except Exception as e:
        logger.warning("Error finding largest files in %s: %s", path, e)
    
    return [{
        'path': str(file.relative_to(path)),
        'size': size,
        'size_human': f"{size / (1024 * 1024):.2f} MB"
    } for file, size in largest[:limit]]


def get_disk_partitions() -> List[Dict]:
    """Get information about all disk partitions."""
    partitions = []
    
    try:
        import psutil
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'opts': partition.opts,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except Exception as e:
                logger.warning("Error getting usage for %s: %s", partition.mountpoint, e)
    except ImportError:
        logger.warning("psutil not available, using basic disk info")
        
    return partitions


@tool(
    name="analyze_disk_usage",
    description="Analyze disk usage and find large files and directories",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="path",
            type=str,
            description="Path to analyze (default: root of all mounted filesystems)",
            required=False,
            default="/"
        ),
        ToolParameter(
            name="max_depth",
            type=int,
            description="Maximum depth to analyze (0 for unlimited)",
            default=3,
            min=0,
            max=10
        ),
        ToolParameter(
            name="include_partitions",
            type=bool,
            description="Include disk partition information",
            default=True
        ),
        ToolParameter(
            name="find_large_files",
            type=bool,
            description="Find largest files in the directory",
            default=True
        ),
        ToolParameter(
            name="large_file_limit",
            type=int,
            description="Number of largest files to find",
            default=50,
            min=1,
            max=1000
        ),
        ToolParameter(
            name="min_file_size_mb",
            type=int,
            description="Minimum file size to consider (in MB)",
            default=10
        )
    ],
    return_type=Dict,
    return_description="Disk usage analysis results"
)
class DiskAnalyzerTool(BaseTool):
    """Tool for analyzing disk usage and finding large files."""
    
    async def execute(self, **kwargs) -> Dict:
        """Execute the disk analysis."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._analyze_sync, **kwargs
        )
    
    def _analyze_sync(
        self,
        path: str = "/",
        max_depth: int = 3,
        include_partitions: bool = True,
        find_large_files: bool = True,
        large_file_limit: int = 50,
        min_file_size_mb: int = 10,
        **kwargs
    ) -> Dict:
        """Synchronous implementation of disk analysis."""
        result = {
            'path': path,
            'status': 'completed'
        }
        
        # Get partition information
        if include_partitions:
            try:
                result['partitions'] = get_disk_partitions()
            except Exception as e:
                logger.error("Error getting partition info: %s", e)
                result['partitions'] = []
        
        # Analyze disk usage
        try:
            usage = get_disk_usage(path, max_depth)
            result['disk_usage'] = usage.to_dict()
        except Exception as e:
            logger.error("Error analyzing disk usage: %s", e)
            result['error'] = f"Failed to analyze disk usage: {e}"
        
        # Find large files
        if find_large_files:
            try:
                min_size = min_file_size_mb * 1024 * 1024
                large_files = get_largest_files(path, large_file_limit)
                result['large_files'] = [
                    f for f in large_files 
                    if f['size'] >= min_size
                ][:large_file_limit]
            except Exception as e:
                logger.error("Error finding large files: %s", e)
                result['error'] = f"Failed to find large files: {e}"
        
        return result
