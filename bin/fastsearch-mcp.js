#!/usr/bin/env node

// npm wrapper for Rust binary
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Find the Rust binary
const binaryName = process.platform === 'win32' ? 'fastsearch.exe' : 'fastsearch';
const binaryPath = path.join(__dirname, '..', 'target', 'release', binaryName);

// Check if binary exists
if (!fs.existsSync(binaryPath)) {
    console.error('FastSearch binary not found. Please run: npm run build');
    process.exit(1);
}

// Pass through all arguments to the Rust binary
const args = process.argv.slice(2);
const child = spawn(binaryPath, args, {
    stdio: 'inherit',
    cwd: process.cwd()
});

child.on('error', (err) => {
    console.error('Failed to start FastSearch:', err);
    process.exit(1);
});

child.on('exit', (code) => {
    process.exit(code || 0);
});