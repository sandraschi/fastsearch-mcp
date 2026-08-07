"""File integrity checker tool for MCP."""

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from fastsearch_mcp.logging_config import get_logger
from fastsearch_mcp.mcp_instance import mcp

logger = get_logger(__name__)

# Default hash algorithm to use
DEFAULT_HASH_ALGORITHM = "sha256"
SUPPORTED_ALGORITHMS = ["md5", "sha1", "sha256", "sha512"]


@dataclass
class FileIntegrityRecord:
    """Data class for file integrity records."""

    path: str
    size: int
    mtime: float
    hash_algorithm: str
    hash_value: str
    last_checked: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert record to dictionary."""
        return {
            "path": self.path,
            "size": self.size,
            "mtime": self.mtime,
            "hash_algorithm": self.hash_algorithm,
            "hash_value": self.hash_value,
            "last_checked": self.last_checked,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileIntegrityRecord":
        """Create record from dictionary."""
        return cls(
            path=data["path"],
            size=data["size"],
            mtime=data["mtime"],
            hash_algorithm=data["hash_algorithm"],
            hash_value=data["hash_value"],
            last_checked=data.get("last_checked", time.time()),
            metadata=data.get("metadata", {}),
        )


class FileIntegrityChecker:
    """File integrity checker that calculates and verifies file hashes."""

    def __init__(self, db_path: str | None = None):
        """Initialize the integrity checker.

        Args:
            db_path: Path to the integrity database file. If None, an in-memory database is used.
        """
        self.db_path = db_path
        self.records: dict[str, FileIntegrityRecord] = {}
        self._load_database()

    def _load_database(self) -> None:
        """Load the integrity database from disk."""
        if not self.db_path or not os.path.exists(self.db_path):
            self.records = {}
            return

        try:
            with open(self.db_path, encoding="utf-8") as f:
                data = json.load(f)
                self.records = {
                    record["path"]: FileIntegrityRecord.from_dict(record) for record in data.get("records", [])
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
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"records": [record.to_dict() for record in self.records.values()]},
                    f,
                    indent=2,
                    default=str,
                )
            logger.debug("Saved %d integrity records to %s", len(self.records), self.db_path)
            return True
        except Exception as e:
            logger.error("Error saving integrity database: %s", e, exc_info=True)
            return False

    def calculate_file_hash(self, file_path: str | Path, algorithm: str = DEFAULT_HASH_ALGORITHM) -> str | None:
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
            with open(file_path, "rb") as f:
                # Read the file in chunks to handle large files
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError as e:
            logger.debug("Error hashing file %s: %s", file_path, e)
            return None

    def add_file(
        self,
        file_path: str | Path,
        algorithm: str = DEFAULT_HASH_ALGORITHM,
        metadata: dict | None = None,
    ) -> FileIntegrityRecord | None:
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
                metadata=metadata or {},
            )

            self.records[file_path] = record
            return record

        except OSError as e:
            logger.debug("Error adding file %s to integrity database: %s", file_path, e)
            return None

    def remove_file(self, file_path: str | Path) -> bool:
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

    def verify_file(self, file_path: str | Path) -> dict:
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
                "status": "not_found",
                "message": "File not found in integrity database",
                "path": file_path,
            }

        record = self.records[file_path]

        # Check if the file exists
        if not os.path.exists(file_path):
            return {
                "status": "missing",
                "message": "File has been deleted or moved",
                "path": file_path,
                "record": record.to_dict(),
            }

        try:
            # Check file size
            stat = os.stat(file_path)
            if stat.st_size != record.size:
                return {
                    "status": "modified",
                    "message": "File size has changed",
                    "path": file_path,
                    "expected_size": record.size,
                    "actual_size": stat.st_size,
                    "record": record.to_dict(),
                }

            # Check modification time (as a quick check before hashing)
            if abs(stat.st_mtime - record.mtime) > 1.0:  # Allow 1 second for time resolution differences
                # File was modified, but we need to verify the content
                pass
            else:
                # File wasn't modified, so the hash should still be valid
                record.last_checked = time.time()
                return {
                    "status": "verified",
                    "message": "File verified (unmodified)",
                    "path": file_path,
                    "record": record.to_dict(),
                }

            # Calculate the current hash
            current_hash = self.calculate_file_hash(file_path, record.hash_algorithm)
            if current_hash is None:
                return {
                    "status": "error",
                    "message": "Could not calculate file hash",
                    "path": file_path,
                    "record": record.to_dict(),
                }

            # Compare hashes
            if current_hash == record.hash_value:
                # Update the record with the new mtime
                record.mtime = stat.st_mtime
                record.last_checked = time.time()

                return {
                    "status": "verified",
                    "message": "File verified (content matches)",
                    "path": file_path,
                    "record": record.to_dict(),
                }
            else:
                return {
                    "status": "modified",
                    "message": "File content has changed",
                    "path": file_path,
                    "expected_hash": record.hash_value,
                    "actual_hash": current_hash,
                    "record": record.to_dict(),
                }

        except OSError as e:
            return {
                "status": "error",
                "message": f"Error verifying file: {e!s}",
                "path": file_path,
                "record": record.to_dict(),
            }

    def scan_directory(
        self,
        directory: str | Path,
        patterns: list[str] | None = None,
        exclude_dirs: list[str] | None = None,
        algorithm: str = DEFAULT_HASH_ALGORITHM,
        update_existing: bool = False,
        max_file_size: int | None = None,
    ) -> dict[str, dict]:
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
        if patterns is None:
            patterns = ["*"]
        directory = Path(directory).resolve()
        results = {
            "scanned_directory": str(directory),
            "total_files": 0,
            "added": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "files": [],
        }

        # Convert exclude_dirs to a set of absolute paths
        exclude_paths = set()
        if exclude_dirs:
            for pattern in exclude_dirs:
                for path in directory.glob("**/" + pattern):
                    if path.is_dir():
                        exclude_paths.add(str(path.resolve()))

        # Process each pattern
        for pattern in patterns:
            for file_path in directory.glob("**/" + pattern):
                # Skip directories and files in excluded directories
                if not file_path.is_file():
                    continue

                # Skip files in excluded directories
                file_path_str = str(file_path.resolve())
                if any(file_path_str.startswith(excluded) for excluded in exclude_paths):
                    results["skipped"] += 1
                    continue

                # Skip files larger than max_file_size
                file_size = file_path.stat().st_size
                if max_file_size is not None and file_size > max_file_size:
                    results["skipped"] += 1
                    continue

                results["total_files"] += 1

                # Check if the file is already in the database
                if file_path_str in self.records and not update_existing:
                    results["skipped"] += 1
                    results["files"].append(
                        {
                            "path": file_path_str,
                            "status": "skipped",
                            "message": "File already in database",
                            "record": self.records[file_path_str].to_dict(),
                        }
                    )
                    continue

                # Add or update the file
                was_present = file_path_str in self.records
                record = self.add_file(file_path, algorithm)
                if record:
                    if was_present and update_existing:
                        results["updated"] += 1
                        status = "updated"
                    else:
                        results["added"] += 1
                        status = "added"

                    results["files"].append({"path": file_path_str, "status": status, "record": record.to_dict()})
                else:
                    results["failed"] += 1
                    results["files"].append(
                        {
                            "path": file_path_str,
                            "status": "failed",
                            "message": "Could not process file",
                        }
                    )

        return results


@mcp.tool
async def check_file_integrity(
    paths: list[str],
    database: str = "~/.fastsearch/integrity_db.json",
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    update: bool = False,
    recursive: bool = True,
    patterns: list[str] | None = None,
    exclude_dirs: list[str] | None = None,
    max_file_size: int = 100,
) -> dict:
    """CHECK_FILE_INTEGRITY — Compare files on disk to a persisted hash database.

    **paths:** Each entry may be a **file** or a **directory**. Files are verified
    directly. Directories are walked when ``recursive`` is True (subject to ``patterns``
    and ``exclude_dirs``). If a path does not exist, behavior depends on the checker:
    missing files referenced only from DB surface as ``missing`` in per-file results;
    completely invalid roots typically yield errors or empty work—prefer validating paths
    before calling.

    **database:** JSON backing store for known-good hashes (default under the user profile).
    User-visible path: expands ``~``. Safe to back up or delete to reset baselines.

    Args:
        paths: One or more absolute or relative filesystem roots to scan or files to verify.
        database: Integrity DB path (JSON). Default: ``~/.fastsearch/integrity_db.json``.
        algorithm: Hash algorithm name (must match what was used to seed the DB).
        update: When True, add or refresh records for files encountered.
        recursive: Directory descent for directory ``paths``.
        patterns: Glob include list for directory walks (default ``*``).
        exclude_dirs: Directory name fragments to skip (e.g. ``.git``, ``node_modules``).
        max_file_size: Skip files larger than this many **MB**; ``0`` = no size cap.

    Returns:
        Aggregates: ``checked``, ``verified``, ``modified``, ``missing``, ``errors``,
        ``details`` (per-path rows), ``summary`` with ``database`` absolute path.

    Recovery: High ``modified``/``missing`` counts → investigate tampering or moved files;
    permission errors appear under ``details`` / ``errors``.
    """
    if patterns is None:
        patterns = ["*"]
    if exclude_dirs is None:
        exclude_dirs = [".git", "__pycache__", "node_modules", ".venv", "venv"]

    db_path = os.path.expanduser(database)
    max_file_size_bytes = max_file_size * 1024 * 1024 if max_file_size > 0 else None

    # Initialize the checker
    checker = FileIntegrityChecker(db_path)

    # Process each path
    results = {
        "checked": 0,
        "verified": 0,
        "modified": 0,
        "missing": 0,
        "errors": 0,
        "details": [],
    }

    for path in paths:
        path = os.path.expanduser(path)

        if os.path.isfile(path):
            # Process a single file
            result = await _process_file_integrity(checker, path, update, algorithm)
            results["checked"] += 1

            if result["status"] == "verified":
                results["verified"] += 1
            elif result["status"] == "modified":
                results["modified"] += 1
            elif result["status"] == "missing":
                results["missing"] += 1
            else:
                results["errors"] += 1

            results["details"].append(result)

        elif os.path.isdir(path) and recursive:
            # Process a directory recursively
            scan_results = await asyncio.to_thread(
                checker.scan_directory,
                path,
                patterns,
                exclude_dirs,
                algorithm,
                update,
                max_file_size_bytes,
            )

            # Verify all files in the scan results
            for file_info in scan_results["files"]:
                if file_info["status"] in ["added", "updated"]:
                    # New or updated files are considered verified
                    results["verified"] += 1
                    results["checked"] += 1
                    results["details"].append(
                        {
                            "path": file_info["path"],
                            "status": "verified",
                            "message": "File added to database",
                            "record": file_info.get("record"),
                        }
                    )
                elif file_info["status"] == "skipped":
                    # For skipped files, verify them
                    result = await _process_file_integrity(checker, file_info["path"], update, algorithm)
                    results["checked"] += 1

                    if result["status"] == "verified":
                        results["verified"] += 1
                    elif result["status"] == "modified":
                        results["modified"] += 1
                    elif result["status"] == "missing":
                        results["missing"] += 1
                    else:
                        results["errors"] += 1

                    results["details"].append(result)

        # Save the database after each path
        checker.save_database()

    # Add a summary
    results["summary"] = {
        "total_checked": results["checked"],
        "verified": results["verified"],
        "modified": results["modified"],
        "missing": results["missing"],
        "errors": results["errors"],
        "database": db_path,
    }

    return results


async def _process_file_integrity(checker: FileIntegrityChecker, file_path: str, update: bool, algorithm: str) -> dict:
    """Process a single file for integrity checking."""
    try:
        # Verify the file
        result = await asyncio.to_thread(checker.verify_file, file_path)

        # If the file is not in the database, add it if update is True
        if result.get("status") == "not_found" and update:
            record = await asyncio.to_thread(checker.add_file, file_path, algorithm)

            if record:
                result = {
                    "path": file_path,
                    "status": "verified",
                    "message": "File added to database",
                    "record": record.to_dict(),
                }

        return result

    except Exception as e:
        return {
            "path": file_path,
            "status": "error",
            "message": f"Error processing file: {e!s}",
        }


@mcp.tool
async def generate_file_hashes(
    paths: list[str],
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    recursive: bool = False,
    patterns: list[str] | None = None,
    exclude_dirs: list[str] | None = None,
) -> dict:
    """Generate hash values for files.

    Calculates cryptographic hash values (checksums) for files using the specified
    algorithm. Supports single files or recursive directory processing. Hash values
    are unique fingerprints that can be used to verify file integrity, detect changes,
    identify duplicates, or verify file authenticity.

    Args:
        paths: List of files or directories to hash. Can include both file paths
            and directory paths. Examples: ["C:\\file.txt"], ["C:\\Projects"],
            ["file1.txt", "file2.txt", "C:\\Data"]. Required: At least one path.

        algorithm: Hash algorithm to use (default: "sha256"). Valid values:
            "md5", "sha1", "sha256", "sha512". SHA256 is recommended for security.
            MD5 is faster but less secure. Examples: "sha256", "md5".

        recursive: Recursively process directories (default: False). When True,
            processes all files in subdirectories. When False, only processes
            files directly in the specified directories (or single files).

        patterns: File patterns to include when processing directories recursively
            (default: None, which includes all files). Examples: ["*.py", "*.txt"],
            ["*.{py,js,ts}"], ["*.log"]. Patterns use glob syntax.

        exclude_dirs: Directories to exclude from recursive search (default: None).
            Default excludes: [".git", "__pycache__", "node_modules"]. Examples:
            [".git", "temp", "cache"], ["**/build", "**/dist"].

    Returns:
        Dictionary containing:
            algorithm: Hash algorithm used (string). Same as the input algorithm
                parameter.

            files: Dictionary mapping file paths to their hash values. Keys are
                absolute file paths (strings), values are hexadecimal hash strings.
                Example: {"C:\\file.txt": "a3b5c7d9e1f2..."}.

            errors: Dictionary mapping file paths to error messages for files that
                failed to hash. Keys are file paths, values are error strings.
                Example: {"C:\\locked.txt": "Permission denied"}.

            summary: Dictionary with operation summary containing:
                - total_files: Total number of files successfully hashed (integer)
                - successful: Number of successful hashes (integer, same as total_files)
                - failed: Number of files that failed to hash (integer)
                - algorithm: Hash algorithm used (string)

    Usage:
        This tool is used when you need to calculate cryptographic hash values
        (checksums) for files. Hash values serve as unique fingerprints that can
        detect if files have been modified, corrupted, or duplicated. It works by
        reading file contents and computing a hash using the specified algorithm.
        Best practices include:
        - Use SHA256 for security-sensitive operations (default)
        - Use MD5 for faster hashing when security isn't critical
        - Use recursive=True with patterns to hash specific file types
        - Exclude build/cache directories to speed up processing

        Common scenarios:
        - Verify downloaded files match published checksums
        - Detect if files have been modified or corrupted
        - Find duplicate files by comparing hash values
        - Create baseline hash database for integrity monitoring
        - Verify file integrity after backup/restore operations
        - Check if files have changed since last verification
        - Generate checksums for file distribution

    Examples:
        Hash a single file:
            results = await generate_file_hashes(
                paths=["C:\\important\\document.pdf"],
                algorithm="sha256"
            )
            # Returns: algorithm, files map, summary (see Returns in docstring).

        Hash all Python files in a directory:
            results = await generate_file_hashes(
                paths=["C:\\Projects"],
                algorithm="sha256",
                recursive=True,
                patterns=["*.py"]
            )
            # Returns: {'algorithm': 'sha256', 'files': {...}, 'summary': {'total_files': 150, ...}}

        Hash multiple files with MD5 (faster):
            results = await generate_file_hashes(
                paths=["file1.txt", "file2.txt", "file3.txt"],
                algorithm="md5"
            )
            # Returns: {'algorithm': 'md5', 'files': {...}, ...}

        Hash directory excluding common build directories:
            results = await generate_file_hashes(
                paths=["C:\\Code"],
                recursive=True,
                exclude_dirs=[".git", "__pycache__", "node_modules", "build", "dist"]
            )
            # Returns: {'algorithm': 'sha256', 'files': {...}, ...}

    Errors:
        Common errors and solutions:
        - Unsupported hash algorithm: Use one of: md5, sha1, sha256, sha512
        - File not found: Ensure file paths exist and are accessible
        - Permission denied: Check file access permissions
        - Directory without recursive: Set recursive=True to process directories
        - Empty paths list: Provide at least one file or directory path

    See Also:
        - find_duplicate_files: Find duplicate files using content hashing
        - fastsearch_search: Find files before hashing
        - fastsearch_search_advanced: Advanced file search with filters
    """
    if patterns is None:
        patterns = ["*"]
    if exclude_dirs is None:
        exclude_dirs = [".git", "__pycache__", "node_modules"]

    if algorithm not in SUPPORTED_ALGORITHMS:
        return {
            "error": f"Unsupported hash algorithm: {algorithm}",
            "supported_algorithms": SUPPORTED_ALGORITHMS,
        }

    results = {"algorithm": algorithm, "files": {}, "errors": {}}

    for path in paths:
        path = os.path.expanduser(path)

        if os.path.isfile(path):
            # Process a single file
            try:
                hash_value = await asyncio.to_thread(_hash_file_sync, path, algorithm)
                results["files"][path] = hash_value
            except Exception as e:
                results["errors"][path] = str(e)

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
                        hash_value = await asyncio.to_thread(_hash_file_sync, file_path_str, algorithm)
                        results["files"][file_path_str] = hash_value
                    except Exception as e:
                        results["errors"][file_path_str] = str(e)

    # Add a summary
    results["summary"] = {
        "total_files": len(results["files"]),
        "successful": len(results["files"]),
        "failed": len(results.get("errors", {})),
        "algorithm": algorithm,
    }

    return results


def _hash_file_sync(file_path: str, algorithm: str) -> str:
    """Calculate the hash of a file (synchronous)."""
    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        # Read the file in chunks to handle large files
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)

    return hasher.hexdigest()
