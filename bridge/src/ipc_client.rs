//! IPC client for communicating with the FastSearch service

use std::io;
use std::time::Duration;

use thiserror::Error;
use tracing::error;
use tokio::{
    io::{AsyncReadExt, AsyncWriteExt},
    net::windows::named_pipe::{ClientOptions, NamedPipeClient},
};

use fastsearch_shared::{SearchRequest, SearchResponse, SearchStats};

/// Timeout for establishing connection to the service
const CONNECTION_TIMEOUT: Duration = Duration::from_secs(2);

/// Timeout for read operations
const READ_TIMEOUT: Duration = Duration::from_secs(30);

/// IPC client for communicating with the FastSearch service
#[derive(Debug)]
pub struct IpcClient {
    client: Option<NamedPipeClient>,
    pipe_name: String,
}

/// Errors that can occur during IPC communication
#[derive(Error, Debug)]
pub enum IpcError {
    /// I/O operation failed
    #[error("I/O error: {0}")]
    Io(#[from] io::Error),
    
    /// Operation timed out
    #[error("Operation timed out")]
    Timeout,
    
    /// Service is not available
    #[error("Service not available")]
    ServiceUnavailable,
    
    /// Service is not running
    #[error("Service not running")]
    ServiceNotRunning,
    
    /// Serialization/deserialization failed
    #[error("Serialization error: {0}")]
    Serialization(#[from] bincode::Error),
    
    /// Protocol error
    #[error("Protocol error: {0}")]
    Protocol(String),
}

impl IpcClient {
    /// Create a new IPC client and connect to the named pipe
    pub async fn new(pipe_name: &str) -> Result<Self, IpcError> {
        let pipe_path = format!(r"\\.\pipe\{pipe_name}");
        
        // Try to connect to the named pipe
        let client = ClientOptions::new()
            .open(&pipe_path)
            .map_err(|e| {
                error!("Failed to connect to pipe {}: {}", pipe_path, e);
                IpcError::ServiceUnavailable
            })?;
            
        Ok(Self {
            client: Some(client),
            pipe_name: pipe_name.to_string(),
        })
    }

    /// Create a disconnected IPC client
    pub fn disconnected() -> Self {
        Self {
            client: None,
            pipe_name: String::new(),
        }
    }
    
    pub async fn get_stats(&self) -> Result<SearchStats, IpcError> {
        // TODO: Get real stats from service
        Ok(SearchStats {
            files_indexed: 1000,
            total_size: 1024 * 1024 * 1024, // 1GB
            last_updated: chrono::Utc::now().timestamp(),
            directories_indexed: 100,
            avg_search_time_ms: Some(10),
            total_searches: Some(5000),
            cache_hit_rate: Some(0.95),
            memory_usage_mb: Some(50),
            uptime_seconds: Some(3600), // 1 hour
            service_running: Some(true),
            ntfs_mode: Some(true),
        })
    }
    
    pub async fn check_service_status(&self) -> Result<bool, IpcError> {
        // Check if we have a client connection
        Ok(self.client.is_some())
    }
    
    /// Send a search request to the FastSearch service
    pub async fn send_request(&self, request: SearchRequest) -> Result<SearchResponse, IpcError> {
        let client = self.client.as_ref().ok_or(IpcError::ServiceNotRunning)?;
        
        // Serialize the request
        let request_bytes = bincode::serialize(&request)?;
            
        // Send the length prefix
        let len = request_bytes.len() as u32;
        let client_ref: &mut NamedPipeClient = unsafe { &mut *(client as *const _ as *mut _) };
        
        client_ref.write_all(&len.to_le_bytes()).await?;
        
        // Send the request data
        client_ref.write_all(&request_bytes).await?;
        
        // Read the response length
        let mut len_buf = [0u8; 4];
        client_ref.read_exact(&mut len_buf).await?;
        let len = u32::from_le_bytes(len_buf) as usize;
        
        // Read the response data
        let mut response_buf = vec![0u8; len];
        client_ref.read_exact(&mut response_buf).await?;
        
        // Deserialize the response
        let response: SearchResponse = bincode::deserialize(&response_buf)?;
            
        Ok(response)
    }
}
