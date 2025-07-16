use clap::{Arg, Command};
use log::{info, error};
use std::io::{self, BufRead, BufReader, Write};
use serde_json::{json, Value};
use anyhow::Result;

mod mcp_server;
mod ntfs_reader;

use crate::mcp_server::McpServer;

fn main() -> Result<()> {
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
                .help("Drive letter to index (e.g., C:)")
                .default_value("C:")
        )
        .arg(
            Arg::new("benchmark")
                .long("benchmark")
                .help("Run performance benchmark")
                .action(clap::ArgAction::SetTrue)
        )
        .get_matches();

    if matches.get_flag("mcp-server") {
        info!("Starting FastSearch MCP Server");
        run_mcp_server()?;
    } else if matches.get_flag("benchmark") {
        let drive = matches.get_one::<String>("drive").unwrap();
        run_benchmark(drive)?;
    } else {
        println!("FastSearch - Lightning-fast file search");
        println!("Use --mcp-server to run as MCP server");
        println!("Use --benchmark to run performance tests");
        println!("Use --drive <letter> to specify drive (default: C:)");
    }

    Ok(())
}

fn run_mcp_server() -> Result<()> {
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

fn run_benchmark(drive: &str) -> Result<()> {
    info!("Running FastSearch benchmark for drive: {}", drive);
    
    #[cfg(windows)]
    {
        // Run NTFS MFT benchmark
        crate::ntfs_reader::benchmark_mft_performance(drive)?;
    }
    
    #[cfg(not(windows))]
    {
        println!("Benchmark is only available on Windows (NTFS required)");
        println!("Drive specified: {}", drive);
        println!("Platform: {}", std::env::consts::OS);
    }
    
    Ok(())
}
