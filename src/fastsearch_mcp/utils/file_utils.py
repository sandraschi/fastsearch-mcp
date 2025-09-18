"""
File utilities for FastSearch MCP.

This module provides file system utilities following FastMCP 2.12 patterns.
"""

import os
import re
from pathlib import Path
from typing import Iterator, List, Optional, Pattern


def find_files(
    pattern: str,
    root_dir: str = ".",
    max_results: int = 100,
    case_sensitive: bool = False
) -> List[str]:
    """
    Find files matching a pattern using direct NTFS MFT access.
    
    Args:
        pattern: Glob pattern to match files
        root_dir: Root directory to search in
        max_results: Maximum number of results to return
        case_sensitive: Whether the search should be case sensitive
        
    Returns:
        List of matching file paths
    """
    # Convert glob pattern to regex
    regex_pattern = _glob_to_regex(pattern)
    if not case_sensitive:
        regex_pattern = re.compile(regex_pattern.pattern, re.IGNORECASE)
    
    results = []
    root_path = Path(root_dir)
    
    try:
        # Use os.walk for now - in production this would use NTFS MFT
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if len(results) >= max_results:
                    break
                    
                file_path = Path(root) / file
                if regex_pattern.search(str(file_path)):
                    results.append(str(file_path))
                    
    except Exception as e:
        # Log error but don't fail completely
        print(f"Error searching files: {e}")
    
    return results


def search_in_file(
    file_path: str,
    pattern: str,
    case_sensitive: bool = False
) -> List[dict]:
    """
    Search for a pattern within a file.
    
    Args:
        file_path: Path to the file to search
        pattern: Pattern to search for
        case_sensitive: Whether the search should be case sensitive
        
    Returns:
        List of matches with line numbers and content
    """
    matches = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if case_sensitive:
                    if pattern in line:
                        matches.append({
                            'line': line_num,
                            'content': line.strip(),
                            'file': file_path
                        })
                else:
                    if pattern.lower() in line.lower():
                        matches.append({
                            'line': line_num,
                            'content': line.strip(),
                            'file': file_path
                        })
    except Exception as e:
        print(f"Error searching in file {file_path}: {e}")
    
    return matches


def _glob_to_regex(glob_pattern: str) -> Pattern[str]:
    """Convert glob pattern to regex pattern."""
    # Simple glob to regex conversion
    regex_pattern = glob_pattern.replace('.', r'\.')
    regex_pattern = regex_pattern.replace('*', '.*')
    regex_pattern = regex_pattern.replace('?', '.')
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
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk
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
            'path': str(path),
            'name': path.name,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'is_file': path.is_file(),
            'is_dir': path.is_dir(),
            'exists': path.exists()
        }
    except Exception as e:
        return {
            'path': file_path,
            'error': str(e),
            'exists': False
        }
