//! This module helps explore the mcp-core API

use mcp_core as mcp;

fn main() {
    // Print all public items in mcp_core
    println!("mcp_core version: {}", env!("CARGO_PKG_VERSION"));
    
    // Try to import and print some types
    println!("\nAvailable types in mcp_core:");
    
    // Server-related types
    println!("\nServer types:");
    println!("  - Server: {}", type_name_of_val(&mcp::Server::new()));
    
    // Try to get types from the types module
    println!("\nTypes module:");
    if let Ok(types) = std::any::type_name_of_val(&mcp::types::Error::new("test")).split("::").next() {
        println!("  - Error: {}", types);
    }
    
    // List all public items in mcp_core
    println!("\nAll public items in mcp_core:");
    let items = get_public_items("mcp_core");
    for item in items {
        println!("  - {}", item);
    }
}

// Helper function to get type name
fn type_name_of_val<T>(_: &T) -> &'static str {
    std::any::type_name::<T>()
}

// Helper function to get public items from a module (simplified)
fn get_public_items(module: &str) -> Vec<String> {
    // This is a simplified version - in a real scenario, you'd use reflection or proc macros
    // For now, we'll just list what we know about
    match module {
        "mcp_core" => vec![
            "Server".to_string(),
            "types".to_string(),
            "types::Error".to_string(),
            // Add more as we discover them
        ],
        _ => vec![],
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_explore() {
        // Just make sure it compiles
        main();
    }
}
