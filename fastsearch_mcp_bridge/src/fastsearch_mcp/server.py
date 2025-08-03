"""FastMCP 2.10 compliant server implementation for FastSearch."""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fastsearch_mcp")


class SearchRequest(BaseModel):
    """Search request model."""
    
    pattern: str = Field(..., description="Search pattern")
    search_type: str = Field("fuzzy", description="Type of search (exact, glob, regex, fuzzy)")
    max_results: int = Field(50, description="Maximum number of results to return")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional search filters")


class SearchResult(BaseModel):
    """Search result model."""
    
    path: str = Field(..., description="File path")
    score: Optional[float] = Field(None, description="Search relevance score")
    size: Optional[int] = Field(None, description="File size in bytes")
    modified: Optional[float] = Field(None, description="Last modified timestamp")
    is_dir: bool = Field(False, description="Whether the path is a directory")


class SearchResponse(BaseModel):
    """Search response model."""
    
    results: List[SearchResult] = Field(default_factory=list, description="List of search results")
    total: int = Field(0, description="Total number of results")
    duration_ms: float = Field(0.0, description="Search duration in milliseconds")


class ServiceStatus(BaseModel):
    """Service status model."""
    
    running: bool = Field(..., description="Whether the service is running")
    version: Optional[str] = Field(None, description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")


class McpError(Exception):
    """Base exception for MCP server errors."""
    
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(self.message)


class McpServer:
    """FastMCP 2.10 compliant server for FastSearch."""
    
    def __init__(self, service_pipe: Optional[str] = None):
        """Initialize the MCP server.
        
        Args:
            service_pipe: Path to the FastSearch service pipe (Windows named pipe)
        """
        self.service_pipe = service_pipe or os.getenv("FASTSEARCH_PIPE", r"\\.\pipe\fastsearch-service")
        self.should_stop = False
        
    async def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming MCP request.
        
        Args:
            method: Method name (e.g., "search", "get_status")
            params: Method parameters
            
        Returns:
            Response data or raises McpError
        """
        handler_name = f"handle_{method}"
        if not hasattr(self, handler_name):
            raise McpError(-32601, f"Method not found: {method}")
        
        handler = getattr(self, handler_name)
        try:
            result = await handler(**params) if asyncio.iscoroutinefunction(handler) else handler(**params)
            return {"result": result.dict() if hasattr(result, 'dict') else result}
        except McpError as e:
            raise e
        except Exception as e:
            logger.exception(f"Error handling method {method}")
            raise McpError(-32603, f"Internal error: {str(e)}")
    
    async def handle_search(self, pattern: str, **kwargs) -> SearchResponse:
        """Handle search request.
        
        Args:
            pattern: Search pattern
            **kwargs: Additional search parameters
            
        Returns:
            SearchResponse with results
        """
        # TODO: Implement actual search using FastSearch service
        logger.info(f"Searching for: {pattern} with params: {kwargs}")
        return SearchResponse(
            results=[],
            total=0,
            duration_ms=0.0,
        )
    
    async def handle_get_status(self) -> ServiceStatus:
        """Get service status.
        
        Returns:
            ServiceStatus with current status
        """
        # TODO: Check if FastSearch service is running
        return ServiceStatus(
            running=False,
            version="1.0.0",
            uptime_seconds=0.0,
        )
    
    async def start(self, stdin=None, stdout=None):
        """Start the MCP server.
        
        Args:
            stdin: Input stream (default: sys.stdin)
            stdout: Output stream (default: sys.stdout)
        """
        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout
        
        logger.info(f"Starting FastSearch MCP bridge (v{__version__})")
        
        try:
            while not self.should_stop:
                # Read request from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, stdin.readline)
                if not line:
                    break
                    
                try:
                    request = json.loads(line)
                    method = request.get("method")
                    params = request.get("params", {})
                    request_id = request.get("id")
                    
                    if not method:
                        raise McpError(-32600, "Invalid request: missing 'method'")
                    
                    # Handle the request
                    try:
                        result = await self.handle_request(method, params)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            **result
                        }
                    except McpError as e:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": e.code,
                                "message": e.message,
                                "data": e.data
                            }
                        }
                    
                    # Write response to stdout
                    stdout.write(json.dumps(response) + "\n")
                    stdout.flush()
                    
                except json.JSONDecodeError:
                    error = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    stdout.write(json.dumps(error) + "\n")
                    stdout.flush()
                except Exception as e:
                    logger.exception("Unexpected error handling request")
                    error = {
                        "jsonrpc": "2.0",
                        "id": request_id if 'request_id' in locals() else None,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    stdout.write(json.dumps(error) + "\n")
                    stdout.flush()
                    
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.exception("Fatal error in MCP server")
            raise
        finally:
            logger.info("MCP server stopped")
