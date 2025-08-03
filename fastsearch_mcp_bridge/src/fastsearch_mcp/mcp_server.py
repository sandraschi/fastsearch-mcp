"""FastMCP 2.10 compliant server implementation for FastSearch."""

import asyncio
import json
import logging
import signal
import sys
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from pydantic import BaseModel, Field, validator

from .ipc import FastSearchClient, IpcError

logger = logging.getLogger(__name__)

# Type aliases
JsonRpcId = Union[str, int, None]
JsonRpcParams = Union[Dict[str, Any], List[Any], None]
Handler = Callable[..., Awaitable[Any]]


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request model."""
    
    jsonrpc: str = Field("2.0", const=True)
    method: str
    params: JsonRpcParams = None
    id: JsonRpcId = None
    
    @validator('jsonrpc')
    def validate_jsonrpc_version(cls, v):
        if v != "2.0":
            raise ValueError("jsonrpc version must be '2.0'")
        return v


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response model."""
    
    jsonrpc: str = Field("2.0", const=True)
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: JsonRpcId
    
    @classmethod
    def success(cls, result: Any, request_id: JsonRpcId):
        return cls(result=result, id=request_id)
    
    @classmethod
    def error(cls, code: int, message: str, data: Any = None, request_id: JsonRpcId = None):
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return cls(error=error, id=request_id)


class McpServer:
    """FastMCP 2.10 compliant server implementation."""
    
    def __init__(self, service_pipe: Optional[str] = None):
        """Initialize the MCP server.
        
        Args:
            service_pipe: Optional custom named pipe for FastSearch service
        """
        self.service_pipe = service_pipe
        self._handlers = {}
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._client = FastSearchClient(pipe_name=service_pipe)
        
        # Register standard MCP methods
        self.register_method("mcp.get_capabilities", self.handle_get_capabilities)
        self.register_method("mcp.ping", self.handle_ping)
        self.register_method("mcp.shutdown", self.handle_shutdown)
        
        # Register FastSearch methods
        self.register_method("fastsearch.search", self.handle_search)
        self.register_method("fastsearch.status", self.handle_status)
    
    def register_method(self, name: str, handler: Handler) -> None:
        """Register a method handler.
        
        Args:
            name: Method name (e.g., "fastsearch.search")
            handler: Async function to handle the method
        """
        self._handlers[name] = handler
    
    async def start(self, stdin=None, stdout=None) -> None:
        """Start the MCP server.
        
        Args:
            stdin: Input stream (default: sys.stdin)
            stdout: Output stream (default: sys.stdout)
        """
        self._running = True
        self._shutdown_event.clear()
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._handle_shutdown_signal, sig)
        
        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout
        
        logger.info("Starting FastSearch MCP server")
        
        try:
            # Connect to the FastSearch service
            try:
                await self._client.connect()
                logger.info("Connected to FastSearch service")
            except IpcError as e:
                logger.error(f"Failed to connect to FastSearch service: {e}")
                # Continue anyway to handle capabilities and other non-service methods
            
            # Main message loop
            while self._running and not self._shutdown_event.is_set():
                try:
                    # Read a line from stdin
                    line = await loop.run_in_executor(None, stdin.readline)
                    if not line:
                        logger.debug("Received EOF on stdin, shutting down")
                        break
                    
                    # Process the request
                    response = await self._process_request(line)
                    if response:
                        # Write the response to stdout
                        await loop.run_in_executor(
                            None, 
                            lambda: stdout.write(json.dumps(response.dict()) + "\n") or stdout.flush()
                        )
                
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    response = JsonRpcResponse.error(
                        -32700, "Parse error", str(e)
                    )
                    await loop.run_in_executor(
                        None, 
                        lambda: stdout.write(json.dumps(response.dict()) + "\n") or stdout.flush()
                    )
                
                except Exception as e:
                    logger.exception("Error processing request")
                    response = JsonRpcResponse.error(
                        -32603, "Internal error", str(e)
                    )
                    await loop.run_in_executor(
                        None, 
                        lambda: stdout.write(json.dumps(response.dict()) + "\n") or stdout.flush()
                    )
        
        except asyncio.CancelledError:
            logger.info("Server task cancelled")
        
        finally:
            # Clean up
            await self._client.disconnect()
            logger.info("FastSearch MCP server stopped")
    
    async def _process_request(self, request_data: str) -> Optional[JsonRpcResponse]:
        """Process a single JSON-RPC request.
        
        Args:
            request_data: Raw JSON-RPC request data
            
        Returns:
            JSON-RPC response, or None for notifications
        """
        try:
            # Parse the request
            try:
                request_dict = json.loads(request_data)
                request = JsonRpcRequest(**request_dict)
            except Exception as e:
                logger.error(f"Invalid request: {e}")
                return JsonRpcResponse.error(
                    -32600, "Invalid Request", str(e)
                )
            
            # Handle notifications (requests without an ID)
            if request.id is None:
                logger.debug(f"Received notification: {request.method}")
                asyncio.create_task(self._execute_handler(request))
                return None
            
            # Handle regular requests
            logger.debug(f"Received request: {request.method} (id: {request.id})")
            try:
                result = await self._execute_handler(request)
                return JsonRpcResponse.success(result, request.id)
            
            except Exception as e:
                logger.exception(f"Error handling {request.method}")
                if isinstance(e, IpcError):
                    return JsonRpcResponse.error(
                        -32000, "Service error", str(e), request.id
                    )
                return JsonRpcResponse.error(
                    -32603, "Internal error", str(e), request.id
                )
        
        except Exception as e:
            logger.exception("Unexpected error processing request")
            return JsonRpcResponse.error(
                -32603, "Internal error", str(e)
            )
    
    async def _execute_handler(self, request: JsonRpcRequest) -> Any:
        """Execute the appropriate handler for a request.
        
        Args:
            request: The JSON-RPC request
            
        Returns:
            The handler's result
            
        Raises:
            Exception: If the handler raises an exception
        """
        handler = self._handlers.get(request.method)
        if not handler:
            raise ValueError(f"Method not found: {request.method}")
        
        # Convert params to kwargs if it's a dict
        params = request.params or {}
        if isinstance(params, dict):
            return await handler(**params)
        else:
            return await handler(*params)
    
    def _handle_shutdown_signal(self, signum, frame=None):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self._shutdown_event.set()
    
    # Standard MCP method handlers
    
    async def handle_get_capabilities(self) -> Dict[str, Any]:
        """Handle mcp.get_capabilities request."""
        return {
            "capabilities": {
                "fastsearch": {
                    "version": "1.0.0",
                    "methods": ["search", "status"],
                    "filters": ["file_type", "size", "modified"],
                    "search_types": ["exact", "glob", "regex", "fuzzy"]
                },
                "mcp": {
                    "version": "2.10.0",
                    "protocol": "jsonrpc2.0"
                }
            }
        }
    
    async def handle_ping(self) -> str:
        """Handle mcp.ping request."""
        return "pong"
    
    async def handle_shutdown(self) -> None:
        """Handle mcp.shutdown request."""
        self._shutdown_event.set()
    
    # FastSearch method handlers
    
    async def handle_search(
        self,
        query: str,
        search_type: str = "fuzzy",
        max_results: int = 50,
        **filters
    ) -> Dict[str, Any]:
        """Handle fastsearch.search request."""
        if not self._client.connected:
            await self._client.connect()
        
        try:
            result = await self._client.search(
                pattern=query,
                search_type=search_type,
                max_results=max_results,
                **filters
            )
            return {
                "results": result.get("results", []),
                "total": result.get("total", 0),
                "duration_ms": result.get("duration_ms", 0)
            }
        except IpcError as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def handle_status(self) -> Dict[str, Any]:
        """Handle fastsearch.status request."""
        if not self._client.connected:
            try:
                await self._client.connect()
            except IpcError as e:
                return {
                    "service_available": False,
                    "service_status": {
                        "running": False,
                        "error": str(e)
                    },
                    "bridge_status": "ready"
                }
        
        try:
            status = await self._client.get_status()
            return {
                "service_available": True,
                "service_status": status,
                "bridge_status": "ready"
            }
        except IpcError as e:
            return {
                "service_available": False,
                "service_status": {
                    "running": False,
                    "error": str(e)
                },
                "bridge_status": "ready"
            }
