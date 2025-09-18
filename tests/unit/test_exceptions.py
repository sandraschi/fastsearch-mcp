"""
Unit tests for FastSearch MCP exceptions.
"""
import pytest
from fastmcp.exceptions import McpError

class TestMcpError:
    """Test McpError and its subclasses."""
    
    def test_mcp_error_basic(self):
        ""Test basic McpError functionality."""
        error = McpError("Test error", code=123, data={"key": "value"})
        assert str(error) == "Test error"
        assert error.code == 123
        assert error.data == {"key": "value"}
        
    def test_mcp_error_to_dict(self):
        ""Test conversion of McpError to dictionary."""
        error = McpError("Test error", code=123, data={"key": "value"})
        error_dict = error.to_dict()
        assert error_dict == {
            'code': 123,
            'message': 'Test error',
            'data': {'key': 'value'}
        }

class TestErrorInheritance:
    """Test custom error inheritance from McpError."""
    
    def test_custom_error(self):
        ""Test creating a custom error that inherits from McpError."""
        class CustomError(McpError):
            """Custom error for testing."""
            
            def __init__(self, message: str, custom_field: str):
                super().__init__(
                    message=message,
                    code=1000,
                    data={"custom_field": custom_field}
                )
                
        error = CustomError("Custom error occurred", "test_value")
        assert isinstance(error, McpError)
        assert error.code == 1000
        assert error.data["custom_field"] == "test_value"
        assert str(error) == "Custom error occurred"
