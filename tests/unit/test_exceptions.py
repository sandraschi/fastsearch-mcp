"""
Unit tests for FastSearch MCP exceptions.
"""

from fastsearch_mcp.exceptions import McpError, NtfsError, PipeError, SearchError, ServiceError


class TestMcpError:
    """Test McpError and its subclasses."""

    def test_mcp_error_basic(self):
        """Test basic McpError functionality."""
        error = McpError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_custom_subclasses(self):
        """Test sub-exception classes."""
        err1 = ServiceError("Service down")
        err2 = NtfsError("MFT error")
        err3 = SearchError("Invalid pattern")
        err4 = PipeError("Pipe error")

        assert isinstance(err1, McpError)
        assert isinstance(err2, McpError)
        assert isinstance(err3, McpError)
        assert isinstance(err4, McpError)
