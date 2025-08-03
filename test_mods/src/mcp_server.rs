//! MCP server module for testing

use crate::search_engine::SearchEngine;

/// Main MCP server that handles requests and delegates to appropriate handlers
pub struct McpServer {
    search_engine: SearchEngine,
}

impl McpServer {
    /// Create a new MCP server instance
    pub fn new() -> Self {
        McpServer {
            search_engine: SearchEngine::new(),
        }
    }

    /// Test method to verify the search engine is working
    pub fn test(&self) -> &'static str {
        self.search_engine.test()
    }
}
