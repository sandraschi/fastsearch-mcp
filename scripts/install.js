// Post-install script to build Rust binary if needed
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('Setting up FastSearch MCP Server...');

const binaryPath = path.join(__dirname, '..', 'target', 'release', 'fastsearch.exe');

// Check if we need to build
if (!fs.existsSync(binaryPath)) {
    console.log('Building FastSearch binary...');
    
    try {
        // Check if we have Rust toolchain
        execSync('cargo --version', { stdio: 'ignore' });
        
        // Build the release binary
        execSync('cargo build --release', { 
            cwd: path.join(__dirname, '..'),
            stdio: 'inherit' 
        });
        
        console.log('✓ FastSearch binary built successfully');
    } catch (error) {
        console.error('❌ Failed to build FastSearch binary');
        console.error('Please ensure Rust toolchain is installed: https://rustup.rs/');
        process.exit(1);
    }
} else {
    console.log('✓ FastSearch binary already exists');
}

console.log('🚀 FastSearch MCP Server ready!');
console.log('Add to claude_desktop_config.json:');
console.log(JSON.stringify({
    mcpServers: {
        fastsearch: {
            command: "fastsearch-mcp",
            args: ["--mcp-server"]
        }
    }
}, null, 2));