"""
FastMCP 2.11.3 compliant server implementation for FastSearch.

This module provides an MCP server that can be extended with custom tools
and follows the MCP 2.11.3 protocol specification.
"""

import asyncio
import inspect
import json
import logging
import signal
import sys
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable, TypeVar, Type, cast

from pydantic import BaseModel, Field, validator, ValidationError

from .ipc import FastSearchClient, IpcError
from .exceptions import McpError
from .tools import ToolRegistry, ToolInfo, tool as tool_decorator

# Get logger
logger = logging.getLogger(__name__)

# Type variables for generic type hints
T = TypeVar('T')

class JsonRpcError(Exception):
    """Base class for JSON-RPC errors."""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

class ParseError(JsonRpcError):
    """Invalid JSON was received by the server."""
    def __init__(self, message: str = "Parse error"):
        super().__init__(-32700, message)

class InvalidRequest(JsonRpcError):
    """The JSON sent is not a valid Request object."""
    def __init__(self, message: str = "Invalid Request"):
        super().__init__(-32600, message)

class MethodNotFound(JsonRpcError):
    """The method does not exist / is not available."""
    def __init__(self, method: str):
        super().__init__(-32601, f"Method not found: {method}")
        self.method = method

class InvalidParams(JsonRpcError):
    """Invalid method parameter(s)."""
    def __init__(self, message: str = "Invalid params"):
        super().__init__(-32602, message)

class InternalError(JsonRpcError):
    """Internal JSON-RPC error."""
    def __init__(self, message: str = "Internal error"):
        super().__init__(-32603, message)

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
    """
    FastMCP 2.11.3 compliant server implementation.
    
    This server handles JSON-RPC 2.0 requests and dispatches them to registered
    tools or methods. It supports both standard MCP methods and custom tools.
    """
    
    def __init__(self, service_pipe: Optional[str] = None, tool_registry: Optional[ToolRegistry] = None):
        """Initialize the MCP server.
        
        Args:
            service_pipe: Optional custom named pipe for FastSearch service
            tool_registry: Optional custom tool registry (uses global registry if None)
        """
        self.service_pipe = service_pipe
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._client = FastSearchClient(pipe_name=service_pipe)
        self._tool_registry = tool_registry or get_global_registry()
        
        # Register standard MCP methods
        self.register_tool("mcp.get_capabilities", self.handle_get_capabilities)
        self.register_tool("mcp.ping", self.handle_ping)
        self.register_tool("mcp.shutdown", self.handle_shutdown)
        
        # Register FastSearch methods
        self.register_tool("fastsearch.search", self.handle_search)
        self.register_tool("fastsearch.status", self.handle_status)
    
    def register_method(self, name: str, handler: Handler) -> None:
        """
        Register a method handler (legacy method).
        
        Args:
            name: Method name (e.g., "fastsearch.search")
            handler: Async function to handle the method
            
        Note:
            Prefer using @tool decorator or register_tool() for new code.
        """
        logger.warning(
            "register_method() is deprecated. Use @tool decorator or register_tool() instead."
        )
        self.register_tool(name, handler)
    
    def register_tool(self, name: str = None, handler: Optional[Handler] = None):
        """
        Register a tool with the server.
        
        Can be used as a decorator or as a regular method.
        
        Examples:
            # As a decorator
            @server.register_tool("example.hello")
            async def hello():
                return "Hello, world!"
                
            # As a regular method
            async def hello():
                return "Hello, world!"
            server.register_tool("example.hello", hello)
        """
        # Handle decorator usage
        if name is not None and handler is None and callable(name):
            func = name
            return tool_decorator(func.__name__.replace('_', '.'))(func)
            
        # Handle direct registration
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError("Handler must be an async function")
            
        # Wrap the handler to provide consistent error handling
        @wraps(handler)
        async def wrapped_handler(**kwargs):
            try:
                return await handler(**kwargs)
            except JsonRpcError as e:
                raise e
            except Exception as e:
                logger.exception(f"Error in tool {name}")
                raise InternalError(str(e)) from e
                
        # Register with the tool registry
        self._tool_registry.register(wrapped_handler, name=name)
        return wrapped_handler
    
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
                            lambda: stdout.write(json.dumps(response) + "\n") or stdout.flush()
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
    
    async def _process_request(self, request_data: str) -> Optional[Dict[str, Any]]:
        """
        Process a single JSON-RPC request or batch of requests.
        
        Args:
            request_data: Raw JSON-RPC request data
            
        Returns:
            JSON-RPC response, or None for notifications
            
        Raises:
            JsonRpcError: For JSON-RPC specific errors
            Exception: For other unexpected errors
        """
        try:
            try:
                request = json.loads(request_data)
            except json.JSONDecodeError as e:
                raise ParseError(f"Invalid JSON: {e}")
                
            # Handle batch requests
            if isinstance(request, list):
                if not request:  # Empty batch
                    raise InvalidRequest("Empty batch request")
                    
                # Process each request in the batch
                responses = []
                for req in request:
                    try:
                        response = await self._process_single_request(req)
                        if response is not None:  # Skip notifications
                            responses.append(response)
                    except JsonRpcError as e:
                        responses.append({
                            "jsonrpc": "2.0",
                            "error": {
                                "code": e.code,
                                "message": e.message,
                                "data": e.data
                            },
                            "id": req.get('id') if isinstance(req, dict) else None
                        })
                        
                return responses if responses else None
                
            return await self._process_single_request(request)
            
        except JsonRpcError as e:
            # Already a JSON-RPC error, just re-raise
            raise e
            
        except Exception as e:
            logger.exception("Unexpected error processing request")
            raise InternalError(f"Internal error: {str(e)}") from e
    
    async def _process_single_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single JSON-RPC request.
        
        Args:
            request: The JSON-RPC request
            
        Returns:
            JSON-RPC response, or None for notifications
            
        Raises:
            JsonRpcError: For JSON-RPC specific errors
            Exception: For other unexpected errors
        """
        try:
            # Parse the request
            try:
                request_dict = request
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
        """
        Execute the appropriate handler for a request.
        
        Args:
            request: The JSON-RPC request
            
        Returns:
            The handler's result
            
        Raises:
            Exception: If the handler raises an exception
        """
        handler = self._tool_registry.get_tool(request.method)
        if not handler:
            raise MethodNotFound(request.method)
        
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
    
    @tool_decorator("mcp.get_capabilities", "Get server capabilities and available tools")
    async def handle_get_capabilities(self) -> Dict[str, Any]:
        """
        Get server capabilities and available tools.
        
        Returns:
            Dictionary containing server capabilities and available tools
        """
        tools = []
        for tool_info in self._tool_registry.list_tools():
            tools.append({
                'name': tool_info.name,
                'description': tool_info.description or "",
                'parameters': tool_info.parameters,
                'returns': tool_info.returns
            })
            
        return {
            "version": "2.11.3",
            "capabilities": {
                "fastsearch": {
                    "version": __version__,
                    "tools": tools
                }
            }
        }
    
    @tool_decorator("mcp.ping", "Simple ping/pong for health checking")
    async def handle_ping(self) -> str:
        """
        Simple ping/pong for health checking.
        
        Returns:
            str: Always returns "pong"
        """
        return "pong"
    
    @tool_decorator("mcp.shutdown", "Gracefully shut down the server")
    async def handle_shutdown(self) -> None:
        """
        Gracefully shut down the server.
        
        This will cause the server to stop accepting new requests and shut down
        after completing any in-progress requests.
        """
        logger.info("Received shutdown request")
        self._shutdown_event.set()
        return None
    
    # FastSearch method handlers
    
    @tool_decorator(
        "fastsearch.search",
        "Execute a search query",
        parameters={
            "query": {"type": "str", "description": "The search query"},
            "search_type": {"type": "str", "default": "fuzzy", "description": "Type of search (fuzzy, exact, regex, glob)"},
            "max_results": {"type": "int", "default": 50, "description": "Maximum number of results to return"},
            "filters": {"type": "dict", "default": {}, "description": "Additional filters to apply"}
        },
        returns={"type": "list", "description": "List of search results"}
    )
    async def handle_search(
        self,
        query: str,
        search_type: str = "fuzzy",
        max_results: int = 50,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Execute a search query against the FastSearch service.
        
        Args:
            query: The search query string
            search_type: Type of search to perform (fuzzy, exact, regex, glob)
            max_results: Maximum number of results to return
            **filters: Additional filters to apply to the search
            
        Returns:
            List of search results
            
        Raises:
            ValueError: If the search fails
        """
        if not query or not isinstance(query, str):
            raise InvalidParams("Query must be a non-empty string")
            
        if search_type not in ["fuzzy", "exact", "regex", "glob"]:
            raise InvalidParams("search_type must be one of: fuzzy, exact, regex, glob")
            
        if not isinstance(max_results, int) or max_results < 1 or max_results > 1000:
            raise InvalidParams("max_results must be an integer between 1 and 1000")
            
        try:
            return await self._client.search(
                query=query,
                search_type=search_type,
                max_results=max_results,
                **filters
            )
        except IpcError as e:
            logger.error(f"Search failed: {e}")
            raise InternalError(f"Search failed: {e}") from e
    
    @tool_decorator("fastsearch.status", "Get the current status of the FastSearch service")
    async def handle_status(self) -> Dict[str, Any]:
        """
        Get the current status of the FastSearch service.
        
        Returns:
            Dictionary containing service status information
            
        Raises:
            InternalError: If the status check fails
        """
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
