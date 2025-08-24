use anyhow::Result;
use clap::{Arg, Command};
use log::{info, error, LevelFilter};
use serde_json;
use simplelog::{Config, WriteLogger};
use std::fs::File;
use std::io::{self, BufRead, Write};
use std::path::Path;
use std::sync::mpsc;
use std::thread;
use std::time::Duration;
use winapi::um::winbase::GetConsoleWindow;
use winapi::um::wincon::FreeConsole;
use windows_service::{
    service::{ServiceAccess, ServiceErrorControl, ServiceInfo, ServiceStartType, ServiceType},
    service_manager::{ServiceManager, ServiceManagerAccess},
};

// Import our MCP status module
mod mcp_status;
use mcp_status::get_service_status;

// Use modules from the fastsearch_service module
use fastmcp_core::server::McpServer;
use fastsearch_service::pipe_server::PipeServer;
use std::sync::Arc;
use tokio::sync::Mutex;

// Service metadata constants
const SERVICE_NAME: &str = "FastSearchService";
const SERVICE_DISPLAY_NAME: &str = "FastSearch NTFS Service";
const SERVICE_DESCRIPTION: &str = "Provides fast NTFS file search capabilities for FastSearch MCP";
const SERVICE_VERSION: &str = env!("CARGO_PKG_VERSION");
const MCP_VERSION: &str = "2.11.3";

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize structured logging
    let log_file = File::create("C:\\ProgramData\\FastSearch\\service.log")?;
    WriteLogger::init(
        LevelFilter::Info,
        Config::builder()
            .add_filter_ignore("h2".to_string(), LevelFilter::Warn)
            .add_filter_ignore("tower".to_string(), LevelFilter::Warn)
            .build(),
        log_file,
    )?;
    
    info!("Starting FastSearch Service v{} (FastMCP {})", SERVICE_VERSION, MCP_VERSION);
    
    // Parse command line arguments
    let matches = Command::new("fastsearch-service")
        .version(SERVICE_VERSION)
        .about("Windows service for FastSearch NTFS operations")
        .version("0.1.0")
        .subcommand_required(true)
        .subcommand(
            Command::new("status")
                .about("Check service status and get detailed information if running")
        )
        .subcommand(
            Command::new("install")
                .about("Install the FastSearch service")
        )
        .subcommand(
            Command::new("uninstall")
                .about("Uninstall the FastSearch service")
        )
        .subcommand(
            Command::new("run")
                .about("Run the service in console mode (for debugging)")
                .arg(
                    Arg::new("port")
                        .short('p')
                        .long("port")
                        .help("Port to run the web API on")
                        .takes_value(true)
                        .default_value("8080")
                        .value_name("PORT")
                )
        )
        .get_matches();

    match matches.subcommand() {
        Some(("status", _)) => check_service_status().await,
        Some(("install", _)) => install_service().await,
        Some(("uninstall", _)) => uninstall_service().await,
        Some(("run", sub_matches)) => {
            let port = sub_matches.value_of("port")
                .and_then(|p| p.parse::<u16>().ok())
                .unwrap_or(8080);
            run_service(port).await
        },
        _ => unreachable!(),
    }
}

async fn install_service() -> Result<()> {
    info!("Installing {} service...", SERVICE_NAME);
    
    let manager = ServiceManager::local_computer(
        None::<&str>,
        ServiceManagerAccess::CREATE_SERVICE,
    )?;
    
    let service_binary_path = std::env::current_exe()?;
    
    let service = manager.create_service(
        &ServiceInfo {
            name: SERVICE_NAME.into(),
            display_name: SERVICE_DISPLAY_NAME.into(),
            service_type: ServiceType::OwnProcess,
            start_type: ServiceStartType::AutoStart,
            error_control: ServiceErrorControl::Normal,
            executable_path: service_binary_path,
            launch_arguments: vec!["run".into()],
            dependencies: vec![],
            account_name: None,
            account_password: None,
        },
        ServiceAccess::CHANGE_CONFIG | ServiceAccess::START,
    )?;
    
    service.set_description(SERVICE_DESCRIPTION)?;
    service.start::<&str>(&[])?;
    
    info!("Service installed and started successfully");
    Ok(())
}

async fn uninstall_service() -> Result<()> {
    info!("Uninstalling {} service...", SERVICE_NAME);
    
    let manager = ServiceManager::local_computer(
        None::<&str>,
        ServiceManagerAccess::CONNECT,
    )?;
    
    let service = manager.open_service(
        SERVICE_NAME,
        ServiceAccess::STOP | ServiceAccess::DELETE,
    )?;
    
    if let Err(e) = service.stop() {
        if !e.raw_os_error().map_or(false, |code| code == 1062) {  // Ignore "service not running"
            return Err(e.into());
        }
    }
    
    service.delete()?;
    info!("Service uninstalled successfully");
    Ok(())
}

async fn run_service(port: u16) -> Result<()> {
    // If we're not running in a console, detach from it
    unsafe {
        if GetConsoleWindow().is_null() {
            FreeConsole();
        }
    }
    
    info!("Starting FastSearch service in console mode...");
    info!("Web API will be available on port {}", port);
    
    // Hide the console window in release mode
    #[cfg(not(debug_assertions))]
    unsafe { FreeConsole(); }
    
    // Start the MCP server in a separate thread
    let (tx, rx) = mpsc::channel();
    let server_handle = thread::spawn(move || {
        if let Err(e) = run_mcp_server() {
            error!("MCP server error: {}", e);
            let _ = tx.send(());
        }
    });
    
    // Start the web API in a separate thread with the specified port
    let web_api_handle = thread::spawn(move || {
        let rt = tokio::runtime::Runtime::new().unwrap();
        if let Err(e) = rt.block_on(run_web_api(port)) {
            error!("Web API error: {}", e);
            let _ = tx.send(());
        }
    });
    
    // Wait for either server to fail or for user to press Enter
    println!("Press Enter to stop the service...");
    thread::spawn(move || {
        let _ = io::stdin().read_line(&mut String::new());
        let _ = tx.send(());
    });
    
    // Wait for a signal to stop
    let _ = rx.recv();
    
    info!("Shutting down FastSearch service...");
    
    Ok(())
}

async fn run_mcp_server() -> Result<()> {
    let server = McpServer::new()?;
    
    // MCP server protocol: read from stdin, write to stdout
    let stdin = io::stdin();
    let mut stdout = io::stdout();
    
    for line in stdin.lock().lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        
        match serde_json::from_str::<Value>(&line) {
            Ok(request) => {
                let response = server.handle_request(request)?;
                let response_str = serde_json::to_string(&response)?;
                writeln!(stdout, "{}", response_str)?;
                stdout.flush()?;
            }
            Err(e) => {
                error!("Failed to parse request: {}", e);
                let error_response = json!({
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                });
                let response_str = serde_json::to_string(&error_response)?;
                writeln!(stdout, "{}", response_str)?;
                stdout.flush()?;
            }
        }
    }
    
    Ok(())
}

async fn run_web_api(port: u16) -> Result<()> {
    use fastsearch_service::{WebApiServer, web_api::WebApiConfig};
    
    // Create a custom config with the specified port
    let config = WebApiConfig {
        port,
        ..Default::default()
    };
    
    let server = WebApiServer::with_config(config)?;
    server.serve().await?;
    
    Ok(())
}

async fn check_service_status() -> Result<()> {
    // Get the service status using our MCP status module
    let status = get_service_status(SERVICE_NAME, SERVICE_DISPLAY_NAME)?;
    
    // Print human-readable status
    println!("Service Status (FastMCP 2.10 Compatible):");
    println!("  Name:           {}", status.service_name);
    println!("  Display Name:   {}", status.display_name);
    println!("  Installed:      {}", status.is_installed);
    println!("  Running:        {}", status.is_running);
    
    if let Some(state) = &status.state {
        println!("  State:          {}", state);
    }
    
    println!("  Pipe Access:    {}", if status.pipe_accessible { "Accessible" } else { "Not accessible" });
    
    if let Some(pid) = status.pid {
        println!("  Process ID:     {}", pid);
    }
    
    if let Some(start_type) = &status.start_type {
        println!("  Start Type:     {}", start_type);
    }
    
    if let Some(path) = &status.binary_path {
        println!("  Binary Path:    {}", path);
    }
    
    println!("  Last Check:     {}", status.last_check);
    
    // Print JSON representation for MCP client consumption
    println!("\nMCP 2.10 Status (JSON):");
    println!("{}", serde_json::to_string_pretty(&status)?);
    
    Ok(())
}

fn run_benchmark(drive: &str) -> Result<()> {
    println!("Benchmark not implemented yet for drive: {}", drive);
    Ok(())
}
