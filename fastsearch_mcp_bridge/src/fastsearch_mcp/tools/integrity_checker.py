"""File integrity checker tool for MCP."""
import asyncio
import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from fastsearch_mcp.tools.base import BaseTool, ToolCategory, ToolParameter, tool
from fastsearch_mcp.logging_config import get_logger
from fastsearch_mcp.utils.file_utils import find_files

logger = get_logger(__name__)

# Default hash algorithm to use
DEFAULT_HASH_ALGORITHM = 'sha256'
SUPPORTED_ALGORITHMS = ['md5', 'sha1', 'sha256', 'sha512']

@dataclass
class FileIntegrityRecord:
    """Data class for file integrity records."""
    path: str
    size: int
    mtime: float
    hash_algorithm: str
    hash_value: str
    last_checked: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert record to dictionary."""
        return {
            'path': self.path,
            'size': self.size,
            'mtime': self.mtime,
            'hash_algorithm': self.hash_algorithm,
            'hash_value': self.hash_value,
            'last_checked': self.last_checked,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileIntegrityRecord':
        """Create record from dictionary."""
        return cls(
            path=data['path'],
            size=data['size'],
            mtime=data['mtime'],
            hash_algorithm=data['hash_algorithm'],
            hash_value=data['hash_value'],
            last_checked=data.get('last_checked', time.time()),
            metadata=data.get('metadata', {})
        )

class FileIntegrityChecker:
    """File integrity checker that calculates and verifies file hashes."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the integrity checker.
        
        Args:
            db_path: Path to the integrity database file. If None, an in-memory database is used.
        """
        self.db_path = db_path
        self.records: Dict[str, FileIntegrityRecord] = {}
        self._load_database()
    
    def _load_database(self) -> None:
        """Load the integrity database from disk."""
        if not self.db_path or not os.path.exists(self.db_path):
            self.records = {}
            return
            
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.records = {
                    record['path']: FileIntegrityRecord.from_dict(record)
                    for record in data.get('records', [])
                }
            logger.info("Loaded %d integrity records from %s", len(self.records), self.db_path)
        except Exception as e:
            logger.error("Error loading integrity database: %s", e, exc_info=True)
            self.records = {}
    
    def save_database(self) -> bool:
        """Save the integrity database to disk.
        
        Returns:
            bool: True if the database was saved successfully, False otherwise.
        """
        if not self.db_path:
            return False
            
        try:
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            
            # Save the database
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {'records': [record.to_dict() for record in self.records.values()]},
                    f,
                    indent=2,
                    default=str
                )
            logger.debug("Saved %d integrity records to %s", len(self.records), self.db_path)
            return True
        except Exception as e:
            logger.error("Error saving integrity database: %s", e, exc_info=True)
            return False
    
    def calculate_file_hash(self, file_path: Union[str, Path], algorithm: str = DEFAULT_HASH_ALGORITHM) -> Optional[str]:
        """Calculate the hash of a file.
        
        Args:
            file_path: Path to the file.
            algorithm: Hash algorithm to use (md5, sha1, sha256, sha512).
            
        Returns:
            str: Hex digest of the file hash, or None if the file couldn't be read.
        """
        if algorithm not in SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
            
        hasher = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                # Read the file in chunks to handle large files
                for chunk in iter(lambda: f.read(65536), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (IOError, OSError) as e:
            logger.debug("Error hashing file %s: %s", file_path, e)
            return None
    
    def add_file(self, file_path: Union[str, Path], algorithm: str = DEFAULT_HASH_ALGORITHM, 
                metadata: Optional[Dict] = None) -> Optional[FileIntegrityRecord]:
        """Add a file to the integrity database.
        
        Args:
            file_path: Path to the file.
            algorithm: Hash algorithm to use.
            metadata: Optional metadata to store with the file.
            
        Returns:
            FileIntegrityRecord: The created record, or None if the file couldn't be processed.
        """
        file_path = str(Path(file_path).resolve())
        
        try:
            stat = os.stat(file_path)
            
            # Calculate the file hash
            hash_value = self.calculate_file_hash(file_path, algorithm)
            if hash_value is None:
                return None
            
            # Create and store the record
            record = FileIntegrityRecord(
                path=file_path,
                size=stat.st_size,
                mtime=stat.st_mtime,
                hash_algorithm=algorithm,
                hash_value=hash_value,
                last_checked=time.time(),
                metadata=metadata or {}
            )
            
            self.records[file_path] = record
            return record
            
        except (IOError, OSError) as e:
            logger.debug("Error adding file %s to integrity database: %s", file_path, e)
            return None
    
    def remove_file(self, file_path: Union[str, Path]) -> bool:
        """Remove a file from the integrity database.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            bool: True if the file was removed, False otherwise.
        """
        file_path = str(Path(file_path).resolve())
        if file_path in self.records:
            del self.records[file_path]
            return True
        return False
    
    def verify_file(self, file_path: Union[str, Path]) -> Dict:
        """Verify the integrity of a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Dict: Verification result with status and details.
        """
        file_path = str(Path(file_path).resolve())
        
        # Check if the file is in the database
        if file_path not in self.records:
            return {
                'status': 'not_found',
                'message': 'File not found in integrity database',
                'path': file_path
            }
        
        record = self.records[file_path]
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return {
                'status': 'missing',
                'message': 'File has been deleted or moved',
                'path': file_path,
                'record': record.to_dict()
            }
        
        try:
            # Check file size
            stat = os.stat(file_path)
            if stat.st_size != record.size:
                return {
                    'status': 'modified',
                    'message': 'File size has changed',
                    'path': file_path,
                    'expected_size': record.size,
                    'actual_size': stat.st_size,
                    'record': record.to_dict()
                }
            
            # Check modification time (as a quick check before hashing)
            if abs(stat.st_mtime - record.mtime) > 1.0:  # Allow 1 second for time resolution differences
                # File was modified, but we need to verify the content
                pass
            else:
                # File wasn't modified, so the hash should still be valid
                record.last_checked = time.time()
                return {
                    'status': 'verified',
                    'message': 'File verified (unmodified)',
                    'path': file_path,
                    'record': record.to_dict()
                }
            
            # Calculate the current hash
            current_hash = self.calculate_file_hash(file_path, record.hash_algorithm)
            if current_hash is None:
                return {
                    'status': 'error',
                    'message': 'Could not calculate file hash',
                    'path': file_path,
                    'record': record.to_dict()
                }
            
            # Compare hashes
            if current_hash == record.hash_value:
                # Update the record with the new mtime
                record.mtime = stat.st_mtime
                record.last_checked = time.time()
                
                return {
                    'status': 'verified',
                    'message': 'File verified (content matches)',
                    'path': file_path,
                    'record': record.to_dict()
                }
            else:
                return {
                    'status': 'modified',
                    'message': 'File content has changed',
                    'path': file_path,
                    'expected_hash': record.hash_value,
                    'actual_hash': current_hash,
                    'record': record.to_dict()
                }
                
        except (IOError, OSError) as e:
            return {
                'status': 'error',
                'message': f'Error verifying file: {str(e)}',
                'path': file_path,
                'record': record.to_dict()
            }
    
    def scan_directory(self, directory: Union[str, Path], 
                      patterns: List[str] = ['*'],
                      exclude_dirs: Optional[List[str]] = None,
                      algorithm: str = DEFAULT_HASH_ALGORITHM,
                      update_existing: bool = False,
                      max_file_size: Optional[int] = None) -> Dict[str, Dict]:
        """Scan a directory and add/update files in the integrity database.
        
        Args:
            directory: Directory to scan.
            patterns: List of file patterns to include (e.g., ['*.py', '*.txt']).
            exclude_dirs: List of directory patterns to exclude.
            algorithm: Hash algorithm to use.
            update_existing: Whether to update existing files in the database.
            max_file_size: Maximum file size to process in bytes (None for no limit).
            
        Returns:
            Dict: Results of the scan with counts of added, updated, and failed files.
        """
        directory = Path(directory).resolve()
        results = {
            'scanned_directory': str(directory),
            'total_files': 0,
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'files': []
        }
        
        # Convert exclude_dirs to a set of absolute paths
        exclude_paths = set()
        if exclude_dirs:
            for pattern in exclude_dirs:
                for path in directory.glob('**/' + pattern):
                    if path.is_dir():
                        exclude_paths.add(str(path.resolve()))
        
        # Process each pattern
        for pattern in patterns:
            for file_path in directory.glob('**/' + pattern):
                # Skip directories and files in excluded directories
                if not file_path.is_file():
                    continue
                    
                # Skip files in excluded directories
                file_path_str = str(file_path.resolve())
                if any(file_path_str.startswith(excluded) for excluded in exclude_paths):
                    results['skipped'] += 1
                    continue
                
                # Skip files larger than max_file_size
                file_size = file_path.stat().st_size
                if max_file_size is not None and file_size > max_file_size:
                    results['skipped'] += 1
                    continue
                
                results['total_files'] += 1
                
                # Check if the file is already in the database
                if file_path_str in self.records and not update_existing:
                    results['skipped'] += 1
                    results['files'].append({
                        'path': file_path_str,
                        'status': 'skipped',
                        'message': 'File already in database',
                        'record': self.records[file_path_str].to_dict()
                    })
                    continue
                
                # Add or update the file
                record = self.add_file(file_path, algorithm)
                if record:
                    if file_path_str in self.records and update_existing:
                        results['updated'] += 1
                        status = 'updated'
                    else:
                        results['added'] += 1
                        status = 'added'
                    
                    results['files'].append({
                        'path': file_path_str,
                        'status': status,
                        'record': record.to_dict()
                    })
                else:
                    results['failed'] += 1
                    results['files'].append({
                        'path': file_path_str,
                        'status': 'failed',
                        'message': 'Could not process file'
                    })
        
        return results


@tool(
    name="check_file_integrity",
    description="Check the integrity of files by verifying their checksums",
    category=ToolCategory.SECURITY,
    parameters=[
        ToolParameter(
            name="paths",
            type=list,
            description="List of files or directories to check",
            required=True
        ),
        ToolParameter(
            name="database",
            type=str,
            description="Path to the integrity database file",
            default="~/.fastsearch/integrity_db.json"
        ),
        ToolParameter(
            name="algorithm",
            type=str,
            description="Hash algorithm to use",
            default=DEFAULT_HASH_ALGORITHM,
            choices=SUPPORTED_ALGORITHMS
        ),
        ToolParameter(
            name="update",
            type=bool,
            description="Update the database with current file hashes",
            default=False
        ),
        ToolParameter(
            name="recursive",
            type=bool,
            description="Recursively check directories",
            default=True
        ),
        ToolParameter(
            name="patterns",
            type=list,
            description="File patterns to include (e.g., ['*.py', '*.txt'])",
            default=["*"]
        ),
        ToolParameter(
            name="exclude_dirs",
            type=list,
            description="Directories to exclude from recursive search",
            default=[".git", "__pycache__", "node_modules", ".venv", "venv"]
        ),
        ToolParameter(
            name="max_file_size",
            type=int,
            description="Maximum file size to process in MB (0 for no limit)",
            default=100,
            min=0
        )
    ],
    return_type=Dict,
    return_description="Integrity check results"
)
class FileIntegrityCheckerTool(BaseTool):
    """Tool for checking file integrity using checksums."""
    
    def __init__(self):
        self.checker = None
        self.db_path = None
    
    async def execute(self, **kwargs) -> Dict:
        """Execute the file integrity check."""
        paths = kwargs.get('paths', [])
        db_path = os.path.expanduser(kwargs.get('database', '~/.fastsearch/integrity_db.json'))
        algorithm = kwargs.get('algorithm', DEFAULT_HASH_ALGORITHM)
        update = kwargs.get('update', False)
        recursive = kwargs.get('recursive', True)
        patterns = kwargs.get('patterns', ["*"])
        exclude_dirs = kwargs.get('exclude_dirs', [])
        max_file_size_mb = kwargs.get('max_file_size', 100)
        max_file_size = max_file_size_mb * 1024 * 1024 if max_file_size_mb > 0 else None
        
        # Initialize the checker
        self.db_path = db_path
        self.checker = FileIntegrityChecker(db_path)
        
        # Process each path
        results = {
            'checked': 0,
            'verified': 0,
            'modified': 0,
            'missing': 0,
            'errors': 0,
            'details': []
        }
        
        for path in paths:
            path = os.path.expanduser(path)
            
            if os.path.isfile(path):
                # Process a single file
                result = await self._process_file(path, update, algorithm)
                results['checked'] += 1
                
                if result['status'] == 'verified':
                    results['verified'] += 1
                elif result['status'] == 'modified':
                    results['modified'] += 1
                elif result['status'] == 'missing':
                    results['missing'] += 1
                else:
                    results['errors'] += 1
                
                results['details'].append(result)
                
            elif os.path.isdir(path) and recursive:
                # Process a directory recursively
                scan_results = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.checker.scan_directory,
                    path,
                    patterns,
                    exclude_dirs,
                    algorithm,
                    update,
                    max_file_size
                )
                
                # Verify all files in the scan results
                for file_info in scan_results['files']:
                    if file_info['status'] in ['added', 'updated']:
                        # New or updated files are considered verified
                        results['verified'] += 1
                        results['checked'] += 1
                        results['details'].append({
                            'path': file_info['path'],
                            'status': 'verified',
                            'message': 'File added to database',
                            'record': file_info.get('record')
                        })
                    elif file_info['status'] == 'skipped':
                        # For skipped files, verify them
                        result = await self._process_file(file_info['path'], update, algorithm)
                        results['checked'] += 1
                        
                        if result['status'] == 'verified':
                            results['verified'] += 1
                        elif result['status'] == 'modified':
                            results['modified'] += 1
                        elif result['status'] == 'missing':
                            results['missing'] += 1
                        else:
                            results['errors'] += 1
                        
                        results['details'].append(result)
            
            # Save the database after each path
            if self.checker:
                self.checker.save_database()
        
        # Add a summary
        results['summary'] = {
            'total_checked': results['checked'],
            'verified': results['verified'],
            'modified': results['modified'],
            'missing': results['missing'],
            'errors': results['errors'],
            'database': self.db_path
        }
        
        return results
    
    async def _process_file(self, file_path: str, update: bool, algorithm: str) -> Dict:
        """Process a single file for integrity checking."""
        if not self.checker:
            return {
                'path': file_path,
                'status': 'error',
                'message': 'Integrity checker not initialized'
            }
        
        try:
            # Verify the file
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.checker.verify_file,
                file_path
            )
            
            # If the file is not in the database, add it if update is True
            if result.get('status') == 'not_found' and update:
                record = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.checker.add_file,
                    file_path,
                    algorithm
                )
                
                if record:
                    result = {
                        'path': file_path,
                        'status': 'verified',
                        'message': 'File added to database',
                        'record': record.to_dict()
                    }
            
            return result
            
        except Exception as e:
            return {
                'path': file_path,
                'status': 'error',
                'message': f'Error processing file: {str(e)}'
            }
    
    def __del__(self):
        """Ensure the database is saved when the tool is destroyed."""
        if hasattr(self, 'checker') and self.checker:
            self.checker.save_database()


@tool(
    name="generate_file_hashes",
    description="Generate hash values for files",
    category=ToolCategory.UTILITIES,
    parameters=[
        ToolParameter(
            name="paths",
            type=list,
            description="List of files or directories to hash",
            required=True
        ),
        ToolParameter(
            name="algorithm",
            type=str,
            description="Hash algorithm to use",
            default=DEFAULT_HASH_ALGORITHM,
            choices=SUPPORTED_ALGORITHMS
        ),
        ToolParameter(
            name="recursive",
            type=bool,
            description="Recursively process directories",
            default=False
        ),
        ToolParameter(
            name="patterns",
            type=list,
            description="File patterns to include (e.g., ['*.py', '*.txt'])",
            default=["*"]
        ),
        ToolParameter(
            name="exclude_dirs",
            type=list,
            description="Directories to exclude from recursive search",
            default=[".git", "__pycache__", "node_modules"]
        )
    ],
    return_type=Dict,
    return_description="Dictionary mapping file paths to their hash values"
)
class FileHasherTool(BaseTool):
    """Tool for generating file hashes."""
    
    async def execute(self, **kwargs) -> Dict:
        """Generate hashes for the specified files."""
        paths = kwargs.get('paths', [])
        algorithm = kwargs.get('algorithm', DEFAULT_HASH_ALGORITHM)
        recursive = kwargs.get('recursive', False)
        patterns = kwargs.get('patterns', ["*"])
        exclude_dirs = kwargs.get('exclude_dirs', [])
        
        if algorithm not in SUPPORTED_ALGORITHMS:
            return {
                'error': f'Unsupported hash algorithm: {algorithm}',
                'supported_algorithms': SUPPORTED_ALGORITHMS
            }
        
        results = {
            'algorithm': algorithm,
            'files': {},
            'errors': {}
        }
        
        for path in paths:
            path = os.path.expanduser(path)
            
            if os.path.isfile(path):
                # Process a single file
                try:
                    hash_value = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self._hash_file,
                        path,
                        algorithm
                    )
                    results['files'][path] = hash_value
                except Exception as e:
                    results['errors'][path] = str(e)
                    
            elif os.path.isdir(path) and recursive:
                # Process a directory recursively
                for pattern in patterns:
                    for file_path in Path(path).rglob(pattern):
                        # Skip directories and files in excluded directories
                        if not file_path.is_file():
                            continue
                            
                        file_path_str = str(file_path.resolve())
                        
                        # Skip files in excluded directories
                        if any(excluded in file_path.parts for excluded in exclude_dirs):
                            continue
                        
                        try:
                            hash_value = await asyncio.get_event_loop().run_in_executor(
                                None,
                                self._hash_file,
                                file_path_str,
                                algorithm
                            )
                            results['files'][file_path_str] = hash_value
                        except Exception as e:
                            results['errors'][file_path_str] = str(e)
        
        # Add a summary
        results['summary'] = {
            'total_files': len(results['files']),
            'successful': len(results['files']),
            'failed': len(results.get('errors', {})),
            'algorithm': algorithm
        }
        
        return results
    
    def _hash_file(self, file_path: str, algorithm: str) -> str:
        """Calculate the hash of a file."""
        hasher = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            # Read the file in chunks to handle large files
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
                
        return hasher.hexdigest()
