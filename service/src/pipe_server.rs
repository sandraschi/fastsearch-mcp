use std::io::{self, Read, Write};
use std::os::windows::io::{AsRawHandle, FromRawHandle};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;
use winapi::um::namedpipeapi::{
    CreateNamedPipeW, ConnectNamedPipe, DisconnectNamedPipe,
    PIPE_ACCESS_DUPLEX, PIPE_TYPE_MESSAGE, PIPE_READMODE_MESSAGE, PIPE_WAIT,
    PIPE_UNLIMITED_INSTANCES, PIPE_REJECT_REMOTE_CLIENTS
};
use winapi::um::winbase::{
    PIPE_ACCEPT_REMOTE_CLIENTS,
    PIPE_ACCEPT_REMOTE_CLIENTS as PIPE_REJECT_REMOTE_CLIENTS_FLAG
};
use winapi::um::fileapi::{FlushFileBuffers, GetFileType, FILE_TYPE_PIPE};
use winapi::shared::minwindef::DWORD;
use winapi::um::handleapi::INVALID_HANDLE_VALUE;
use winapi::um::winnt::HANDLE;
use winapi::um::winbase::{
    SetFileCompletionNotificationModes, FILE_SKIP_COMPLETION_PORT_ON_SUCCESS,
    FILE_SKIP_SET_EVENT_ON_HANDLE
};
use winapi::um::errhandlingapi::GetLastError;
use winapi::shared::winerror::{
    ERROR_PIPE_CONNECTED, ERROR_NO_DATA, ERROR_BROKEN_PIPE, ERROR_PIPE_NOT_CONNECTED
};
use log::{info, error, warn};
use anyhow::{Result, Context};

const PIPE_NAME: &str = r"\\.\pipe\fastsearch-service";
const BUFFER_SIZE: usize = 65536; // 64KB buffer
const MAX_INSTANCES: DWORD = 10;

pub struct PipeServer {
    pipe_name: String,
    shutdown_tx: Option<mpsc::Sender<()>>,
}

impl PipeServer {
    pub fn new() -> Result<Self> {
        Ok(Self {
            pipe_name: PIPE_NAME.to_string(),
            shutdown_tx: None,
        })
    }

    pub fn run(&mut self) -> Result<()> {
        let (tx, rx) = mpsc::channel();
        self.shutdown_tx = Some(tx);

        info!("Starting named pipe server on {}", self.pipe_name);

        // Create a thread to handle incoming connections
        let pipe_name = self.pipe_name.clone();
        let _handle = thread::spawn(move || {
            if let Err(e) = Self::run_pipe_server(&pipe_name, rx) {
                error!("Pipe server error: {}", e);
            }
        });

        Ok(())
    }

    fn run_pipe_server(pipe_name: &str, shutdown_rx: mpsc::Receiver<()>) -> Result<()> {
        loop {
            // Check for shutdown signal
            if shutdown_rx.try_recv().is_ok() {
                info!("Shutting down pipe server");
                break;
            }

            // Create a new pipe instance
            let pipe_handle = unsafe { Self::create_pipe(pipe_name) }?;
            
            // Connect to the pipe
            match unsafe { ConnectNamedPipe(pipe_handle, std::ptr::null_mut()) } {
                0 => {
                    let last_error = unsafe { GetLastError() };
                    if last_error != ERROR_PIPE_CONNECTED as DWORD {
                        error!("Failed to connect to pipe: {}", last_error);
                        unsafe { winapi::um::handleapi::CloseHandle(pipe_handle) };
                        continue;
                    }
                }
                _ => {}
            }

            info!("Client connected to pipe");
            
            // Handle the client connection in a new thread
            let pipe_handle_copy = unsafe { std::mem::transmute_copy(&pipe_handle) };
            thread::spawn(move || {
                if let Err(e) = Self::handle_client(pipe_handle_copy) {
                    error!("Error handling client: {}", e);
                }
                unsafe { winapi::um::handleapi::CloseHandle(pipe_handle_copy) };
            });
        }

        Ok(())
    }

    unsafe fn create_pipe(pipe_name: &str) -> Result<HANDLE> {
        let wide_name: Vec<u16> = pipe_name.encode_utf16().chain(std::iter::once(0)).collect();

        let pipe_mode = PIPE_READMODE_MESSAGE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS_FLAG;
        
        let pipe_handle = CreateNamedPipeW(
            wide_name.as_ptr(),
            PIPE_ACCESS_DUPLEX | FILE_SKIP_COMPLETION_PORT_ON_SUCCESS | FILE_SKIP_SET_EVENT_ON_HANDLE,
            pipe_mode,
            MAX_INSTANCES,
            BUFFER_SIZE as u32,
            BUFFER_SIZE as u32,
            0, // default timeout
            std::ptr::null_mut() // default security attributes
        );

        if pipe_handle == INVALID_HANDLE_VALUE {
            return Err(io::Error::last_os_error())
                .with_context(|| format!("Failed to create named pipe: {}", pipe_name));
        }

        Ok(pipe_handle)
    }

    fn handle_client(pipe_handle: HANDLE) -> Result<()> {
        let mut buffer = vec![0u8; BUFFER_SIZE];
        let pipe = unsafe { std::fs::File::from_raw_handle(pipe_handle as *mut _) };
        let mut pipe = std::io::BufReader::with_capacity(BUFFER_SIZE, pipe);

        loop {
            match pipe.read(&mut buffer) {
                Ok(0) => break, // Connection closed by client
                Ok(bytes_read) => {
                    // Process the message
                    let message = &buffer[..bytes_read];
                    if let Ok(message_str) = std::str::from_utf8(message) {
                        info!("Received message: {}", message_str);
                        // TODO: Process the message and generate response
                        let response = format!("Processed: {}", message_str);
                        if let Err(e) = pipe.get_mut().write_all(response.as_bytes()) {
                            error!("Failed to send response: {}", e);
                            break;
                        }
                        if let Err(e) = pipe.get_mut().flush() {
                            error!("Failed to flush pipe: {}", e);
                            break;
                        }
                    } else {
                        error!("Received invalid UTF-8 message");
                    }
                }
                Err(ref e) if e.kind() == io::ErrorKind::WouldBlock => {
                    // No data available, check for shutdown or continue
                    thread::sleep(Duration::from_millis(100));
                    continue;
                }
                Err(e) => {
                    error!("Error reading from pipe: {}", e);
                    break;
                }
            }
        }

        info!("Client disconnected");
        Ok(())
    }
}

impl Drop for PipeServer {
    fn drop(&mut self) {
        if let Some(tx) = self.shutdown_tx.take() {
            // Send shutdown signal
            let _ = tx.send(());
        }
    }
}
