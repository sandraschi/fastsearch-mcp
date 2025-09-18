"""
Test utilities for FastSearch MCP tests.
"""
import asyncio
from contextlib import contextmanager
from typing import Any, AsyncGenerator, Callable, Dict, Optional, Type, TypeVar
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import McpError

T = TypeVar('T')

class AsyncContextManager:
    """Helper class for creating async context managers in tests."""
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def async_return(result=None) -> asyncio.Future:
    """Create a mock async function that returns a result."""
    future = asyncio.Future()
    future.set_result(result)
    return future

def async_raise(exception: Exception) -> asyncio.Future:
    """Create a mock async function that raises an exception."""
    future = asyncio.Future()
    future.set_exception(exception)
    return future

@contextmanager
def assert_raises_mcp_error(
    expected_code: Optional[int] = None,
    expected_message: Optional[str] = None,
    expected_data: Optional[Dict[str, Any]] = None
):
    """Context manager to assert that a McpError is raised with specific attributes."""
    try:
        yield
        pytest.fail("Expected McpError was not raised")
    except McpError as e:
        if expected_code is not None:
            assert e.code == expected_code, f"Expected code {expected_code}, got {e.code}"
        if expected_message is not None:
            assert expected_message in str(e), f"Expected message containing '{expected_message}', got '{str(e)}'"
        if expected_data is not None:
            assert e.data == expected_data, f"Expected data {expected_data}, got {e.data}"

def create_mock_coroutine(return_value: Any = None, side_effect: Exception = None) -> AsyncMock:
    """Create a mock coroutine with the specified return value or side effect."""
    if side_effect is not None:
        async def mock_coroutine(*args, **kwargs):
            raise side_effect
    else:
        async def mock_coroutine(*args, **kwargs):
            return return_value
            
    return AsyncMock(side_effect=mock_coroutine)

def mock_async_method(method: Callable[..., T], return_value: Any = None, 
                     side_effect: Exception = None) -> AsyncMock:
    """Mock an async method with the specified return value or side effect."""
    mock = create_mock_coroutine(return_value, side_effect)
    return patch.object(method, mock)
