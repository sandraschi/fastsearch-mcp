// Web API bridge for FastSearch MCP Server
// Exposes MCP functionality as HTTP endpoints for frontend integration

use axum::{
    extract::Query,
    http::Method,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::Arc;
use tower_http::cors::{Any, CorsLayer};
use anyhow::Result;

use crate::McpServer;

/// Configuration for the Web API server
#[derive(Debug, Clone)]
pub struct WebApiConfig {
    /// The port to bind the server to
    pub port: u16,
    /// Whether to enable CORS
    pub enable_cors: bool,
    /// Default number of results to return if not specified
    pub default_max_results: usize,
}

impl Default for WebApiConfig {
    fn default() -> Self {
        Self {
            port: 8080,  // Default port
            enable_cors: true,
            default_max_results: 100,
        }
    }
}

#[derive(Deserialize)]
pub struct SearchRequest {
    pub pattern: String,
    pub path: Option<String>,
    pub max_results: Option<usize>,
}

#[derive(Serialize)]
pub struct SearchResponse {
    pub success: bool,
    pub results: Vec<FileResult>,
    pub count: usize,
    pub search_time_ms: f64,
    pub message: Option<String>,
}

#[derive(Serialize)]
pub struct FileResult {
    pub name: String,
    pub path: String,
    pub full_path: String,
    pub size: u64,
    pub is_directory: bool,
    pub size_formatted: String,
}

#[derive(Serialize)]
pub struct StatusResponse {
    pub success: bool,
    pub status: String,
    pub message: String,
}

pub struct WebApiServer {
    server: Arc<McpServer>,
    config: WebApiConfig,
}

impl WebApiServer {
    /// Create a new Web API server with default configuration
    pub fn new() -> Result<Self> {
        Self::with_config(WebApiConfig::default())
    }
    
    /// Create a new Web API server with custom configuration
    pub fn with_config(config: WebApiConfig) -> Result<Self> {
        Ok(Self {
            server: Arc::new(McpServer::new()?),
            config,
        })
    }
    
    /// Get the current configuration
    pub fn config(&self) -> &WebApiConfig {
        &self.config
    }

    pub async fn serve(self) -> Result<()> {
        // Set up CORS
        let cors = if self.config.enable_cors {
            CorsLayer::new()
                .allow_methods([Method::GET, Method::POST])
                .allow_headers(Any)
                .allow_origin(Any)
        } else {
            // No CORS if disabled
            CorsLayer::new()
        };

        // Build our application with routes
        let app = Router::new()
            .route("/api/search", post(search_files))
            .route("/api/status", get(get_status))
            .route("/api/benchmark", post(benchmark_search))
            .route("/health", get(health_check))
            .layer(cors)
            .with_state(Arc::new(self));

        // Run the server
        let addr = std::net::SocketAddr::from(([127, 0, 0, 1], self.config.port));
        info!("Web API server listening on http://{}", addr);
        
        // Print the server URL for easy access
        println!("FastSearch Web API server running at http://{}", addr);
        
        axum::Server::bind(&addr)
            .serve(app.into_make_service())
            .await?;

        Ok(())
    }
}

async fn search_files(
    axum::extract::State(server): axum::extract::State<Arc<WebApiServer>>,
    Json(request): Json<SearchRequest>,
) -> Json<SearchResponse> {
    let start_time = std::time::Instant::now();

    // Convert to MCP request format
    let mut args = json!({
        "pattern": request.pattern,
        "max_results": request.max_results.unwrap_or(1000)
    });

    if let Some(path) = request.path {
        args["path"] = json!(path);
    }

    // Call MCP server
    match server.mcp_server.fast_search(&args) {
        Ok(_mcp_response) => {
            let search_time = start_time.elapsed().as_millis() as f64;
            
            // Parse MCP response - for now just return success
            Json(SearchResponse {
                success: true,
                count: 0,
                results: vec![],
                search_time_ms: search_time,
                message: Some("Direct search completed".to_string()),
            })
        }
        Err(e) => Json(SearchResponse {
            success: false,
            results: vec![],
            count: 0,
            search_time_ms: start_time.elapsed().as_millis() as f64,
            message: Some(format!("Search failed: {}", e)),
        }),
    }
}

async fn get_status(
    axum::extract::State(_server): axum::extract::State<Arc<WebApiServer>>,
) -> Json<StatusResponse> {
    Json(StatusResponse {
        success: true,
        status: "ready".to_string(),
        message: "FastSearch MCP Server running in direct search mode".to_string(),
    })
}

async fn benchmark_search(
    axum::extract::State(server): axum::extract::State<Arc<WebApiServer>>,
    Query(params): Query<HashMap<String, String>>,
) -> Json<Value> {
    let drive = params.get("drive").unwrap_or(&"C".to_string()).clone();
    
    match server.mcp_server.benchmark_search(&json!({"drive": drive})) {
        Ok(response) => Json(response),
        Err(e) => Json(json!({
            "success": false,
            "error": format!("Benchmark failed: {}", e)
        })),
    }
}

async fn health_check() -> Json<Value> {
    Json(json!({
        "status": "healthy",
        "service": "FastSearch MCP Server",
        "version": "0.1.0",
        "mode": "direct_search"
    }))
}
