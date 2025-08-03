//! MCP (Model-Controller-Presenter) server implementation for FastSearch

use anyhow::Result;
use serde_json::{json, Value};

// Use the search_engine module as declared in lib.rs
use crate::search_engine::SearchEngine;

/// Main MCP server that handles requests and delegates to appropriate handlers
pub struct McpServer {
    search_engine: SearchEngine,
}

impl McpServer {
    /// Create a new MCP server instance
    pub fn new() -> Result<Self> {
        Ok(Self {
            search_engine: SearchEngine::new()?,
        })
    }

    /// Handle an incoming MCP request
    pub fn handle_request(&self, request: Value) -> Result<Value> {
        let method = request["method"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing or invalid method"))?;

        match method {
            "initialize" => self.handle_initialize(request),
            "tools/list" => self.handle_tools_list(),
            _ => Err(anyhow::anyhow!("Unknown method: {}", method)),
        }
    }

    /// Handle initialization request
    fn handle_initialize(&self, _request: Value) -> Result<Value> {
        Ok(json!({
            "result": {
                "capabilities": {
                    "textDocumentSync": 1,
                    "completionProvider": {},
                    "definitionProvider": true,
                    "documentSymbolProvider": true,
                    "workspace": {
                        "workspaceFolders": {
                            "supported": true,
                            "changeNotifications": true
                        }
                    }
                }
            }
        }))
    }

    /// Handle tools/list request
    fn handle_tools_list(&self) -> Result<Value> {
        self.search_engine.handle_tools_list()
    }
    
    /// Perform a fast search with the given arguments
    pub fn fast_search(&self, args: &Value) -> Result<Value> {
        self.search_engine.fast_search(args)
    }
    
    /// Run a benchmark search with the given arguments
    pub fn benchmark_search(&self, args: &Value) -> Result<Value> {
        self.search_engine.benchmark_search(args)
    }
}
