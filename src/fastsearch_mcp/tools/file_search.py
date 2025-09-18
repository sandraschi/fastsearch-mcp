"""File content search tool for MCP."""
import asyncio
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Set, Union

from fastsearch_mcp.tools.base import (
    BaseTool, ToolCategory, ToolParameter, tool
)
from fastsearch_mcp.utils.file_utils import find_files, search_in_file


@tool(
    name="file_content_search",
    description="Search for text patterns in files",
    category=ToolCategory.FILESYSTEM,
    parameters=[
        ToolParameter(
            name="search_pattern",
            type=str,
            description="Pattern to search for (supports regex)",
            required=True
        ),
        ToolParameter(
            name="search_dir",
            type=str,
            description="Directory to search in",
            required=True
        ),
        ToolParameter(
            name="file_pattern",
            type=str,
            description="Pattern to filter files (e.g., '*.txt' or '*.{py,js}')",
            default="*"
        ),
        ToolParameter(
            name="exclude_dirs",
            type=list,
            description="List of directory patterns to exclude",
            default=["**/__pycache__", "**/.git", "**/node_modules"]
        ),
        ToolParameter(
            name="case_sensitive",
            type=bool,
            description="Case-sensitive search",
            default=False
        ),
        ToolParameter(
            name="whole_word",
            type=bool,
            description="Match whole words only",
            default=False
        ),
        ToolParameter(
            name="max_results",
            type=int,
            description="Maximum number of results to return",
            default=100
        ),
        ToolParameter(
            name="context_lines",
            type=int,
            description="Number of context lines to include around matches",
            default=2
        ),
        ToolParameter(
            name="max_file_size_mb",
            type=int,
            description="Maximum file size in MB to search",
            default=10
        ),
        ToolParameter(
            name="skip_binary",
            type=bool,
            description="Skip binary files",
            default=True
        ),
    ],
    return_type=Dict[str, Any],
    return_description="Search results with file paths and matches"
)
class FileContentSearchTool(BaseTool):
    """Tool for searching text patterns in files."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the file content search."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._search_sync, **kwargs
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
        **kwargs
    ) -> Dict[str, Any]:
        """Synchronous implementation of file search."""
        if exclude_dirs is None:
            exclude_dirs = []
            
        search_path = Path(search_dir).expanduser().resolve()
        
        if not search_path.exists() or not search_path.is_dir():
            return {
                "error": f"Directory not found: {search_dir}",
                "matches": []
            }
        
        # Convert file pattern to regex for find_files
        file_regex = (
            file_pattern
            .replace(".", "\\.")
            .replace("*", ".*")
            .replace("?", ".")
            .replace(",", "|")
            .replace("{", "(")
            .replace("}", ")")
        )
        
        # Convert exclude_dirs to regex pattern
        exclude_pattern = "|\\.".join(
            re.escape(d).replace("*", ".*").replace("?", ".") 
            for d in exclude_dirs
        )
        
        # Find all matching files
        files = list(find_files(
            root_dir=search_path,
            include=file_regex,
            exclude=exclude_pattern,
            max_size=max_file_size_mb * 1024 * 1024,
            skip_binary=skip_binary
        ))
        
        if not files:
            return {
                "status": "no_files_found",
                "files_searched": 0,
                "matches": []
            }
        
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
                    max_matches=max_results - total_matches
                )
                
                if matches:
                    rel_path = file_path.relative_to(search_path)
                    results.append({
                        "file": str(rel_path),
                        "path": str(file_path),
                        "matches": [{
                            "line": m["line"],
                            "start": m["start"],
                            "end": m["end"],
                            "match": m["match"],
                            "line_content": m["line_content"],
                            "context": m["context"]
                        } for m in matches]
                    })
                    total_matches += len(matches)
                    
            except Exception as e:
                print(f"Error searching in {file_path}: {e}")
                continue
                
            files_searched += 1
            
            # Update progress periodically
            if files_searched % 100 == 0:
                print(f"Searched {files_searched}/{len(files)} files, found {total_matches} matches...")
        
        return {
            "status": "completed",
            "files_searched": files_searched,
            "total_files": len(files),
            "total_matches": total_matches,
            "matches": results[:max_results]
        }
