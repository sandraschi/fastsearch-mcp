use clap::{Arg, Command};
use log::{info, error};
use std::io::{self, BufRead, Write};
use serde_json::{json, Value};
use anyhow::Result;

// Use modules from the fastsearch_service module
use fastsearch_service::mcp_server::McpServer;

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();
    
    let matches = Command::new("fastsearch")
        .about("Lightning-fast file search using NTFS Master File Table")
        .version("0.1.0")
        .arg(
            Arg::new("mcp-server")
                .long("mcp-server")
                .help("Run as MCP server")
                .action(clap::ArgAction::SetTrue)
        )
        .arg(
            Arg::new("drive")
                .short('d')
                .long("drive")
                .help("NTFS drive letter to search (e.g., C:). The drive must be formatted with NTFS.")
                .default_value("C:")
        )
        .arg(
            Arg::new("benchmark")
                .long("benchmark")
                .help("Run performance benchmark")
                .action(clap::ArgAction::SetTrue)
        )
        .arg(
            Arg::new("web-api")
                .long("web-api")
                .help("Run as web API server for frontend integration")
                .action(clap::ArgAction::SetTrue)
        )
        .get_matches();

    match matches.subcommand() {
        Some(("mcp", _)) => run_mcp_server().await,
        Some(("benchmark", sub_matches)) => {
            let drive = sub_matches.get_one::<String>("drive").unwrap();
            run_benchmark(drive).await
        },
        Some(("web", _)) => run_web_api().await,
        _ => {
            println!("No valid subcommand provided. Use --help for usage information.");
            Ok(())
        }
    }
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

async fn run_benchmark(drive: &str) -> Result<()> {
    info!("Running benchmark on drive {}...", drive);
    fastsearch_service::ntfs_reader::benchmark_mft_performance(drive)?;
    Ok(())
}

async fn run_web_api() -> Result<()> {
    info!("Starting web API server...");
    let server = fastsearch_service::web_api::WebApiServer::new()?;
    server.serve().await?;
    Ok(())
}
