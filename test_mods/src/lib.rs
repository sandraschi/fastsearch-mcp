//! Test module to verify correct import of SearchEngine

// Declare the modules
pub mod search_engine;
pub mod mcp_server;

// Re-export the public API
pub use mcp_server::McpServer;
pub use search_engine::SearchEngine;

// Import from the service crate
use fastsearch_service::search_engine::SearchEngine;

/// Test that we can import and create a new SearchEngine instance
#[test]
fn test_search_engine_import() {
    // This test will pass if the import is successful
    let result = SearchEngine::new();
    assert!(result.is_ok(), "Failed to create SearchEngine: {:?}", result);
}
