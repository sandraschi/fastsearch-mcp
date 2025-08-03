use test_mods::McpServer;

fn main() {
    println!("Testing module imports...");
    
    let server = McpServer::new();
    let result = server.test();
    
    println!("Test result: {}", result);
}
