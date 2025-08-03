//! This module helps explore the mcp-core API

use mcp_core;

fn main() {
    println!("Exploring mcp-core API...");
    
    // List all public items in mcp_core
    println!("\nPublic items in mcp_core:");
    println!("  - Server");
    println!("  - types");
    println!("  - types::Error");
    
    // Print version info
    println!("\nVersion: {}", env!("CARGO_PKG_VERSION"));
    
    // Print path to the crate
    if let Ok(manifest_dir) = std::env::var("CARGO_MANIFEST_DIR") {
        println!("\nManifest directory: {}", manifest_dir);
    }
    
    // Try to list public methods on Server if possible
    println!("\nNote: Run 'cargo doc --open -p mcp-core' to view full documentation");
}
