//! Compatibility layer for FastMCP 2.10 functionality

use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use std::error::Error;
use std::fmt;

/// Simplified MCP error type
#[derive(Debug)]
pub enum McpError {
    Internal(String),
    InvalidParams(String),
    NotFound,
}

impl fmt::Display for McpError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            McpError::Internal(msg) => write!(f, "Internal error: {}", msg),
            McpError::InvalidParams(msg) => write!(f, "Invalid parameters: {}", msg),
            McpError::NotFound => write!(f, "Not found"),
        }
    }
}

impl Error for McpError {}

/// Simplified MCP server
pub struct McpServer {
    pub name: String,
    pub version: String,
    pub description: String,
    tools: HashMap<String, McpTool>,
}

/// Simplified MCP tool definition
pub struct McpTool {
    pub name: String,
    pub description: String,
    pub handler: Box<dyn Fn(serde_json::Value) -> Result<serde_json::Value, McpError> + Send + Sync>,
}

impl McpServer {
    /// Create a new MCP server
    pub fn new(name: impl Into<String>, version: impl Into<String>, description: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            version: version.into(),
            description: description.into(),
            tools: HashMap::new(),
        }
    }

    /// Add a tool to the server
    pub fn add_tool<F>(mut self, name: &str, description: &str, handler: F) -> Self
    where
        F: Fn(serde_json::Value) -> Result<serde_json::Value, McpError> + 'static + Send + Sync,
    {
        self.tools.insert(
            name.to_string(),
            McpTool {
                name: name.to_string(),
                description: description.to_string(),
                handler: Box::new(handler),
            },
        );
        self
    }

    /// Handle an incoming request
    pub fn handle_request(&self, request: &str) -> String {
        // Parse the request
        let req: serde_json::Value = match serde_json::from_str(request) {
            Ok(req) => req,
            Err(e) => return self.error_response("ParseError", &e.to_string(), None),
        };

        // Extract method and params
        let method = req["method"].as_str().unwrap_or("");
        let params = req["params"].clone();
        let id = req["id"].clone();

        // Find and call the handler
        match self.tools.get(method) {
            Some(tool) => match (tool.handler)(params) {
                Ok(result) => self.success_response(&id, result),
                Err(e) => self.error_response("ExecutionError", &e.to_string(), Some(id)),
            },
            None => self.error_response("MethodNotFound", &format!("Method '{}' not found", method), Some(id)),
        }
    }

    fn success_response(&self, id: &serde_json::Value, result: serde_json::Value) -> String {
        let response = serde_json::json!({
            "jsonrpc": "2.0",
            "id": id,
            "result": result
        });
        response.to_string()
    }

    fn error_response(&self, code: &str, message: &str, id: Option<serde_json::Value>) -> String {
        let error = serde_json::json!({
            "code": code,
            "message": message
        });

        let response = serde_json::json!({
            "jsonrpc": "2.0",
            "id": id,
            "error": error
        });

        response.to_string()
    }

    /// Run the server on stdin/stdout
    pub fn run_stdio(self) -> ! {
        use std::io::{self, BufRead};
        
        let stdin = io::stdin();
        for line in stdin.lock().lines() {
            let line = match line {
                Ok(line) => line,
                Err(_) => continue,
            };

            let response = self.handle_request(&line);
            println!("{}", response);
        }
        
        std::process::exit(0);
    }
}
