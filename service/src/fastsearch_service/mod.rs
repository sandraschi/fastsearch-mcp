//! FastSearch MCP Service - Core functionality for high-performance file search

// Re-export public API
pub use crate::fastsearch_service::{
    cache_persistence,
    file_types::*,
    mcp_server::*,
    mft_cache::{FileEntry, MftCache, MftCacheConfig, CacheStats},
    ntfs_reader::*,
    search_engine::*,
    usn_journal::UsnJournalMonitor,
    web_api::*,
};

// Internal modules
mod cache_persistence;
mod file_types;
mod mcp_server;
mod mft_cache;
mod ntfs_reader;
mod search_engine;
mod usn_journal;
mod web_api;

// Only include tests in test builds
#[cfg(test)]
mod mft_cache_tests;
