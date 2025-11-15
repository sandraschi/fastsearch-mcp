#!/usr/bin/env node
/**
 * FastSearch MCP - NPX Entry Point
 * 
 * This script allows FastSearch MCP to be run via NPX:
 *   npx fastsearch-mcp
 * 
 * For IDEs: Cursor, Windsurf, Zed, etc.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Find Python executable
function findPython() {
  const pythonCommands = ['python3', 'python'];
  
  for (const cmd of pythonCommands) {
    try {
      const { execSync } = require('child_process');
      execSync(`${cmd} --version`, { stdio: 'ignore' });
      return cmd;
    } catch (e) {
      // Continue to next command
    }
  }
  
  throw new Error('Python not found. Please install Python 3.8+ and ensure it is in your PATH.');
}

// Find the Python module
function findPythonModule() {
  // When installed via npm, the Python source is in the package
  const packageDir = __dirname;
  const srcPath = path.join(packageDir, '..', 'src', 'fastsearch_mcp');
  
  if (fs.existsSync(srcPath)) {
    // Development/local installation
    return 'fastsearch_mcp';
  }
  
  // Try installed package
  try {
    require.resolve('fastsearch_mcp');
    return 'fastsearch_mcp';
  } catch (e) {
    throw new Error(
      'FastSearch MCP Python package not found. ' +
      'Please install it: pip install fastsearch-mcp'
    );
  }
}

// Main execution
function main() {
  const python = findPython();
  const module = findPythonModule();
  
  // Set environment variables
  const env = {
    ...process.env,
    PYTHONUNBUFFERED: '1',
  };
  
  // Add src to PYTHONPATH if in development
  const packageDir = path.join(__dirname, '..');
  const srcDir = path.join(packageDir, 'src');
  if (fs.existsSync(srcDir)) {
    env.PYTHONPATH = srcDir + (env.PYTHONPATH ? path.delimiter + env.PYTHONPATH : '');
  }
  
  // Spawn Python process
  const args = ['-m', module];
  const child = spawn(python, args, {
    stdio: 'inherit',
    env: env,
    shell: false
  });
  
  child.on('error', (error) => {
    console.error(`Failed to start FastSearch MCP: ${error.message}`);
    process.exit(1);
  });
  
  child.on('exit', (code) => {
    process.exit(code || 0);
  });
  
  // Handle signals
  process.on('SIGINT', () => {
    child.kill('SIGINT');
  });
  
  process.on('SIGTERM', () => {
    child.kill('SIGTERM');
  });
}

if (require.main === module) {
  main();
}

module.exports = { main };
