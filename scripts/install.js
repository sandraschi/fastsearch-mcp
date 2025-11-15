// Post-install script to build the C++ service binary if needed
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('Setting up FastSearch MCP Server...');

const serviceDir = path.join(__dirname, '..', 'service');
const buildDir = path.join(serviceDir, 'build');
const binaryPath = path.join(buildDir, 'bin', 'Release', 'FastSearchServiceNew.exe');

// Check if we need to build
if (!fs.existsSync(binaryPath)) {
    console.log('Building FastSearch service binary...');

    try {
        execSync('cmake -S . -B build -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release', {
            cwd: serviceDir,
            stdio: 'inherit'
        });
        execSync('cmake --build build --config Release', {
            cwd: serviceDir,
            stdio: 'inherit'
        });

        console.log('✓ FastSearch service built successfully');
    } catch (error) {
        console.error('❌ Failed to build FastSearch service');
        console.error('Ensure Visual Studio Build Tools and CMake are installed and available on PATH.');
        process.exit(1);
    }
} else {
    console.log('✓ FastSearch service binary already exists');
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