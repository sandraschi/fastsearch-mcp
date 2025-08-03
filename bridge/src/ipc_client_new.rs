//! IPC client for communicating with the FastSearch service

use std::io;
use std::path::Path;
use std::time::Duration;

use serde::{de::DeserializeOwned, Serialize};
use thiserror::Error;
use tokio::{
    io::{AsyncReadExt, AsyncWriteExt},
    net::windows::named_pipe::{ClientOptions, NamedPipeClient},
    time,
};

use crate::types::*;

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
        let pipe_path = format!(r"\\.\pipe\{}", pipe_name.trim_start_matches(r"\\.\pipe\"));
        
        let client = match time::timeout(
            CONNECTION_TIMEOUT,
            ClientOptions::new().open(&pipe_path),
        )
        .await
        {
            Ok(Ok(client)) => {
                debug_assert_eq!(
                    client.client_process_id(),
                    None,
                    "Connected to pipe but couldn't verify service process"
                );
                Some(client)
            }
            Ok(Err(e)) if e.kind() == io::ErrorKind::NotFound => None,
            Ok(Err(e)) => return Err(e.into()),
            Err(_) => return Err(IpcError::Timeout),
        };

        Ok(Self {
            client,
            pipe_name: pipe_path,
        })
    }

    /// Create a disconnected IPC client
    pub fn disconnected() -> Self {
        Self {
            client: None,
            pipe_name: String::new(),
        }
    }

    /// Check if the client is connected to the service
    pub fn is_connected(&self) -> bool {
        self.client.is_some()
    }

    /// Execute a search request
    pub async fn search(&mut self, request: &SearchRequest) -> Result<SearchResponse, IpcError> {
        self.send_request(1, request).await
    }

    /// Get search statistics
    pub async fn get_stats(&mut self) -> Result<SearchStats, IpcError> {
        self.send_request(2, &()).await
    }

    /// Get the current service status
    pub async fn get_status(&self) -> ServiceStatus {
        match &self.client {
            Some(_) => ServiceStatus::Running,
            None => ServiceStatus::Stopped,
        }
    }

    /// Send a request to the service and wait for a response
    async fn send_request<T: Serialize, R: DeserializeOwned>(
        &mut self,
        opcode: u8,
        data: &T,
    ) -> Result<R, IpcError> {
        let client = match &mut self.client {
            Some(client) => client,
            None => return Err(IpcError::ServiceUnavailable),
        };

        // Serialize the request
        let request = bincode::serialize(&(opcode, data))?;
        
        // Send the request length (4 bytes, little-endian)
        let len = request.len() as u32;
        time::timeout(READ_TIMEOUT, client.write_all(&len.to_le_bytes()))
            .await
            .map_err(|_| IpcError::Timeout)??;
        
        // Send the request data
        time::timeout(READ_TIMEOUT, client.write_all(&request))
            .await
            .map_err(|_| IpcError::Timeout)??;
        
        // Read the response length (4 bytes, little-endian)
        let mut len_buf = [0u8; 4];
        time::timeout(READ_TIMEOUT, client.read_exact(&mut len_buf))
            .await
            .map_err(|_| IpcError::Timeout)??;
            
        let len = u32::from_le_bytes(len_buf) as usize;
        
        // Read the response data
        let mut response_buf = vec![0u8; len];
        time::timeout(READ_TIMEOUT, client.read_exact(&mut response_buf))
            .await
            .map_err(|_| IpcError::Timeout)??;
        
        // Deserialize the response
        let response: Result<R, String> = bincode::deserialize(&response_buf)?;
        response.map_err(IpcError::Protocol)
    }
}
