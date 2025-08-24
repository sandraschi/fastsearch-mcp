use anyhow::Result;
use clap::Parser;
use serde_json::Value;
use std::io::{self, Write};
use winapi::um::{
    fileapi::CreateFileW,
    handleapi::INVALID_HANDLE_VALUE,
    winbase::GENERIC_READ,
    fileapi::OPEN_EXISTING,
    winnt::FILE_SHARE_READ,
};
use std::ffi::OsStr;
use std::os::windows::ffi::OsStrExt;
use std::ptr::null_mut;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Output format (text or json)
    #[arg(short, long, default_value = "text")]
    format: String,
    
    /// Service name to check (default: FastSearchService)
    #[arg(short, long, default_value = "FastSearchService")]
    service: String,
    
    /// Display name for the service (default: FastSearch NTFS Service)
    #[arg(long, default_value = "FastSearch NTFS Service")]
    display_name: String,
}

fn main() -> Result<()> {
    let args = Args::parse();
    
    // Get the service status
    let status = get_service_status(&args.service, &args.display_name)?;
    
    // Output based on format
    match args.format.to_lowercase().as_str() {
        "json" => {
            println!("{}", serde_json::to_string_pretty(&status)?);
        }
        "text" | _ => {
            print_status_text(&status)?;
        }
    }
    
    // Set exit code based on service status
    std::process::exit(if status.is_installed && status.is_running && status.pipe_accessible {
        0  // Success
    } else {
        1  // Service not running or not accessible
    });
}

fn print_status_text(status: &ServiceStatus) -> Result<()> {
    let stdout = io::stdout();
    let mut handle = stdout.lock();
    
    writeln!(handle, "FastSearch MCP 2.10 Status")?;
    writeln!(handle, "=========================\n")?;
    
    writeln!(handle, "Service Information:")?;
    writeln!(handle, "  Name:           {}", status.service_name)?;
    writeln!(handle, "  Display Name:   {}", status.display_name)?;
    writeln!(handle, "  Installed:      {}", status.is_installed)?;
    writeln!(handle, "  Running:        {}", status.is_running)?;
    
    if let Some(state) = &status.state {
        writeln!(handle, "  State:          {}", state)?;
    }
    
    writeln!(handle, "  Pipe Access:    {}", 
        if status.pipe_accessible { "Accessible" } else { "Not accessible" })?;
    
    if let Some(pid) = status.pid {
        writeln!(handle, "  Process ID:     {}", pid)?;
    }
    
    if let Some(start_type) = &status.start_type {
        writeln!(handle, "  Start Type:     {}", start_type)?;
    }
    
    if let Some(path) = &status.binary_path {
        writeln!(handle, "  Binary Path:    {}", path)?;
    }
    
    writeln!(handle, "  Last Check:     {}", status.last_check)?;
    
    // Add a summary line for quick assessment
    writeln!(handle, "\nStatus Summary: {}", 
        if status.is_installed && status.is_running && status.pipe_accessible {
            "✅ Service is running and accessible"
        } else if status.is_installed && status.is_running {
            "⚠️  Service is running but pipe is not accessible"
        } else if status.is_installed {
            "❌ Service is installed but not running"
        } else {
            "❌ Service is not installed"
        })?;
    
    Ok(())
}

// This is a simplified version of the status check that doesn't require admin privileges
fn get_service_status(service_name: &str, display_name: &str) -> Result<ServiceStatus> {
    let is_installed = is_service_installed(service_name);
    let is_running = is_service_running(service_name);
    let pipe_accessible = is_pipe_accessible("fastsearch-service");
    
    // Get additional service info if we can
    let (state, pid, start_type, binary_path) = if is_installed {
        get_service_details(service_name)
    } else {
        (None, None, None, None)
    };
    
    Ok(ServiceStatus {
        service_name: service_name.to_string(),
        display_name: display_name.to_string(),
        is_installed,
        is_running,
        pipe_accessible,
        state,
        pid,
        start_type,
        binary_path,
        last_check: chrono::Local::now().to_rfc3339(),
    })
}

fn is_service_installed(service_name: &str) -> bool {
    use windows_service::{
        service_manager::{ServiceManager, ServiceManagerAccess},
    };
    
    if let Ok(manager) = ServiceManager::local_computer(None::<&str>, ServiceManagerAccess::CONNECT) {
        if let Ok(_) = manager.open_service(service_name, windows_service::service::ServiceAccess::QUERY_STATUS) {
            return true;
        }
    }
    false
}

fn is_service_running(service_name: &str) -> bool {
    use windows_service::{
        service::{ServiceAccess, ServiceState},
        service_manager::{ServiceManager, ServiceManagerAccess},
    };
    
    if let Ok(manager) = ServiceManager::local_computer(None::<&str>, ServiceManagerAccess::CONNECT) {
        if let Ok(service) = manager.open_service(service_name, ServiceAccess::QUERY_STATUS) {
            if let Ok(status) = service.query_status() {
                return status.current_state == ServiceState::Running;
            }
        }
    }
    false
}

fn get_service_details(service_name: &str) -> (Option<String>, Option<u32>, Option<String>, Option<String>) {
    use windows_service::{
        service::{ServiceAccess, ServiceState},
        service_manager::{ServiceManager, ServiceManagerAccess},
    };
    
    if let Ok(manager) = ServiceManager::local_computer(None::<&str>, ServiceManagerAccess::CONNECT) {
        if let Ok(service) = manager.open_service(
            service_name, 
            ServiceAccess::QUERY_STATUS | ServiceAccess::QUERY_CONFIG
        ) {
            let mut state = None;
            let mut pid = None;
            let mut start_type = None;
            let mut binary_path = None;
            
            if let Ok(status) = service.query_status() {
                state = Some(format!("{:?}", status.current_state));
                pid = status.process_id;
            }
            
            if let Ok(config) = service.query_config() {
                start_type = Some(format!("{:?}", config.start_type));
                binary_path = Some(config.executable_path.display().to_string());
            }
            
            return (state, pid, start_type, binary_path);
        }
    }
    
    (None, None, None, None)
}

fn is_pipe_accessible(pipe_name: &str) -> bool {
    let pipe_path = format!(r"\\.\pipe\{}", pipe_name);
    let wide: Vec<u16> = OsStr::new(&pipe_path).encode_wide().chain(Some(0)).collect();
    
    let handle = unsafe {
        CreateFileW(
            wide.as_ptr(),
            GENERIC_READ,
            FILE_SHARE_READ,
            null_mut(),
            OPEN_EXISTING,
            0,
            null_mut()
        )
    };
    
    if handle != INVALID_HANDLE_VALUE {
        unsafe { winapi::um::handleapi::CloseHandle(handle); }
        true
    } else {
        false
    }
}

// Service status structure matching the one in mcp_status.rs
#[derive(serde::Serialize)]
struct ServiceStatus {
    service_name: String,
    display_name: String,
    is_installed: bool,
    is_running: bool,
    pipe_accessible: bool,
    state: Option<String>,
    pid: Option<u32>,
    start_type: Option<String>,
    binary_path: Option<String>,
    last_check: String,
}

// Add this to Cargo.toml:
// [[bin]]
// name = "mcp-status"
// path = "src/bin/mcp-status.rs"
