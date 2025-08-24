"""File system utilities for MCP tools."""
import os
import re
from pathlib import Path
from typing import BinaryIO, Callable, Dict, Iterable, Iterator, List, Optional, Pattern, Set, Tuple, Union

from fastsearch_mcp.logging_config import get_logger

logger = get_logger(__name__)

# Common binary file extensions to skip by default
BINARY_EXTENSIONS = {
    # Executables and libraries
    '.exe', '.dll', '.so', '.dylib', '.a', '.lib', '.o', '.obj',
    # Archives
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar', '.iso',
    # Media
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
    '.mp3', '.wav', '.ogg', '.flac', '.aac',
    '.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # Virtual machine and container files
    '.vmdk', '.vdi', '.vhd', '.vhdx', '.qcow2', '.ova', '.ovf',
    # Database files
    '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.mdf', '.ldf',
    # Other binary formats
    '.dat', '.bin', '.pkl', '.pickle', '.class', '.pyc', '.pyo', '.pyd',
    '.woff', '.woff2', '.eot', '.ttf', '.otf',
}

# Common text file extensions
TEXT_EXTENSIONS = {
    '.txt', '.md', '.markdown', '.rst',
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
    '.go', '.rs', '.rb', '.php', '.sh', '.bash', '.zsh', '.fish',
    '.html', '.css', '.scss', '.sass', '.less',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.xml', '.csv', '.tsv',
    '.log', '.sql', '.dockerfile',
}

def is_binary_file(file_path: Union[str, Path], check_content: bool = True) -> bool:
    """Check if a file is binary.
    
    Args:
        file_path: Path to the file
        check_content: If True, check file content for binary data
        
    Returns:
        bool: True if the file is binary, False otherwise
    """
    # Check by extension first (faster)
    ext = os.path.splitext(str(file_path))[1].lower()
    if ext in BINARY_EXTENSIONS:
        return True
    if ext in TEXT_EXTENSIONS:
        return False
    
    # If extension is not in either set, check file content
    if not check_content:
        return False
        
    try:
        with open(file_path, 'rb') as f:
            # Read first 8KB to check for binary content
            chunk = f.read(8192)
            # Check for null bytes or non-text characters
            return b'\x00' in chunk or not all(32 <= b <= 126 or b in {9, 10, 13} for b in chunk)
    except (IOError, OSError):
        logger.warning("Could not read file: %s", file_path)
        return True

def find_files(
    root_dir: Union[str, Path],
    include: Optional[Union[str, Pattern]] = None,
    exclude: Optional[Union[str, Pattern]] = None,
    max_depth: Optional[int] = None,
    min_size: int = 0,
    max_size: Optional[int] = None,
    file_types: Optional[Set[str]] = None,
    skip_binary: bool = True,
) -> Iterator[Path]:
    """Find files matching the given criteria.
    
    Args:
        root_dir: Directory to search in
        include: Regex pattern to include files
        exclude: Regex pattern to exclude files
        max_depth: Maximum depth to search
        min_size: Minimum file size in bytes
        max_size: Maximum file size in bytes
        file_types: Set of file extensions to include (with leading .)
        skip_binary: Whether to skip binary files
        
    Yields:
        Path: Path to matching files
    """
    root_path = Path(root_dir).resolve()
    
    if isinstance(include, str):
        include_re = re.compile(include)
    else:
        include_re = include
        
    if isinstance(exclude, str):
        exclude_re = re.compile(exclude)
    else:
        exclude_re = exclude
    
    for root, dirs, files in os.walk(root_path):
        # Apply max depth
        if max_depth is not None:
            depth = Path(root).relative_to(root_path).as_posix().count('/') + 1
            if depth > max_depth:
                continue
        
        for filename in files:
            file_path = Path(root) / filename
            
            # Skip broken symlinks
            if not file_path.exists():
                continue
                
            # Skip directories (shouldn't happen with os.walk, but just in case)
            if file_path.is_dir():
                continue
                
            # Skip binary files if requested
            if skip_binary and is_binary_file(file_path):
                continue
                
            # Apply include/exclude patterns
            rel_path = file_path.relative_to(root_path).as_posix()
            if include_re and not include_re.search(rel_path):
                continue
            if exclude_re and exclude_re.search(rel_path):
                continue
                
            # Check file size
            try:
                size = file_path.stat().st_size
                if size < min_size:
                    continue
                if max_size is not None and size > max_size:
                    continue
            except OSError:
                continue
                
            # Check file extension
            if file_types:
                ext = file_path.suffix.lower()
                if ext not in file_types:
                    continue
                    
            yield file_path

def search_in_file(
    file_path: Union[str, Path],
    pattern: Union[str, Pattern],
    encoding: str = 'utf-8',
    errors: str = 'replace',
    context_lines: int = 0,
    case_sensitive: bool = False,
    whole_word: bool = False,
    max_matches: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Search for a pattern in a file.
    
    Args:
        file_path: Path to the file to search in
        pattern: Regex pattern or string to search for
        encoding: File encoding
        errors: How to handle encoding errors
        context_lines: Number of context lines to include around each match
        case_sensitive: Whether the search is case-sensitive
        whole_word: Whether to match whole words only
        max_matches: Maximum number of matches to return per file
        
    Returns:
        List of matches with line numbers and context
    """
    if not os.path.isfile(file_path):
        return []
        
    # Compile the pattern
    if isinstance(pattern, str):
        flags = 0 if case_sensitive else re.IGNORECASE
        if whole_word:
            pattern = fr'\b{re.escape(pattern)}\b'
        try:
            pattern = re.compile(pattern, flags)
        except re.error as e:
            logger.warning("Invalid regex pattern '%s': %s", pattern, e)
            return []
    
    matches = []
    
    try:
        with open(file_path, 'r', encoding=encoding, errors=errors) as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines, 1):
            line_matches = list(pattern.finditer(line))
            if not line_matches:
                continue
                
            # Get the line content and strip any trailing newline
            line_content = line.rstrip('\r\n')
            
            # Get context lines if requested
            context = {}
            if context_lines > 0:
                start = max(0, i - context_lines - 1)
                end = min(len(lines), i + context_lines)
                
                # Get before context
                before = []
                for j in range(start, i - 1):
                    before.append({
                        'line': j + 1,
                        'content': lines[j].rstrip('\r\n')
                    })
                
                # Get after context
                after = []
                for j in range(i, end):
                    after.append({
                        'line': j + 1,
                        'content': lines[j].rstrip('\r\n')
                    })
                
                context = {
                    'before': before,
                    'after': after
                }
            
            # Add each match in the line
            for match in line_matches:
                matches.append({
                    'line': i,
                    'start': match.start(),
                    'end': match.end(),
                    'match': match.group(),
                    'line_content': line_content,
                    'context': context
                })
                
                # Stop if we've reached the maximum number of matches
                if max_matches is not None and len(matches) >= max_matches:
                    return matches
                    
    except (IOError, UnicodeDecodeError) as e:
        logger.warning("Error reading file %s: %s", file_path, e)
        
    return matches
