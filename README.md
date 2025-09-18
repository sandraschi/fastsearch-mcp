# FastSearch MCP

⚡ Lightning-fast file search for Claude Desktop using direct NTFS Master File Table access

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.12%2B-brightgreen)](https://docs.anthropic.com/claude/docs/mcp)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/yourusername/fastsearch-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/yourusername/fastsearch-mcp/actions)

> **Performance**: Scans 1M+ files/second on modern SSDs with minimal memory overhead

## 🚀 Features

- **Blazing Fast**: Direct NTFS Master File Table access for maximum performance
- **Low Resource Usage**: Minimal memory footprint even with millions of files
- **Real-time Indexing**: Immediate file system changes detection
- **Advanced Search**: Support for regex, wildcards, and complex queries
- **Robust Error Handling**: Graceful degradation and comprehensive logging
- **Asynchronous I/O**: Non-blocking operations for maximum throughput

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Windows 10/11 with NTFS file system
- Visual C++ Build Tools (for some dependencies)
- Git (for development)

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/fastsearch-mcp.git
cd fastsearch-mcp

# Install with pip (recommended)
pip install -e ".[dev]"  # For development
# or for production
pip install .
```

### Dependencies

All dependencies are listed in `requirements-dev.txt`. For production, only the following are required:
- fastmcp>=2.11.3
- pydantic>=1.10.0
- pywin32>=305 (Windows only)
- psutil>=5.9.0
- typing-extensions>=4.0.0

## 🛠 Development Setup

### Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fastsearch-mcp.git
   cd fastsearch-mcp
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Unix/macOS
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e ".[dev]"
   ```

### Running the Server

To start the FastSearch MCP server for development:

```bash
python start_server.py
```

This will start the server with default settings. Use `--help` to see available options.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=fastsearch_mcp --cov-report=html

# Run a specific test file
pytest tests/test_mcp_server.py -v
```

### Code Style

We use Black for code formatting and isort for import sorting:

```bash
black .
isort .
```

### Linting

```bash
flake8 .
mypy .
```

## 🏗 Project Structure

```
fastsearch-mcp/
├── fastsearch_mcp_bridge/     # Main package
│   ├── src/
│   │   └── fastsearch_mcp/   # Python package
│   │       ├── __init__.py   # Package initialization
│   │       ├── __main__.py   # Command-line interface
│   │       ├── mcp_server.py # MCP server implementation
│   │       ├── ipc.py        # Inter-process communication
│   │       ├── tools/        # MCP tools
│   │       └── utils/        # Utility functions
│   └── tests/                # Test suite
│       ├── unit/             # Unit tests
│       └── integration/      # Integration tests
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
├── .github/                  # GitHub workflows
├── pyproject.toml            # Project configuration
├── requirements-dev.txt      # Development dependencies
└── README.md                 # This file
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Workflow

1. Create an issue describing the bug or feature
2. Assign the issue to yourself if you're working on it
3. Create a feature branch from `main`
4. Write tests for your changes
5. Ensure all tests pass and code is properly formatted
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastMCP](https://docs.anthropic.com/claude/docs/mcp) - For the Model Control Protocol
- [NTFS](https://en.wikipedia.org/wiki/NTFS) - For the amazing file system
- [pywin32](https://github.com/mhammond/pywin32) - For Windows API bindings

## 📊 Performance

| Metric | Performance |
|--------|-------------|
| Initial Scan | 1,000,000+ files/second |
| Cached Access | 10,000,000+ files/second |
| Memory Usage | ~100MB base + ~10MB per 1M files |
| Threads | Auto-scales with CPU cores (up to 16) |
| Cache Size | Configurable, default 1M entries |
pytest

# Run with coverage
pytest --cov=fastsearch_mcp --cov-report=html

# Run specific test file
pytest tests/unit/test_exceptions.py -v
```

### Code Style

We use Black for code formatting and isort for import sorting:

```bash
black .
isort .
```

## 📝 Project Structure

```
fastsearch-mcp/
├── fastsearch_mcp/          # Main package
│   ├── __init__.py
│   ├── mcp_server.py        # MCP server implementation
│   ├── tools/               # MCP tools
│   └── utils/               # Utility functions
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── conftest.py          # Test fixtures
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

- [FastMCP](https://docs.anthropic.com/claude/docs/mcp) - For the Model Control Protocol
- [NTFS](https://en.wikipedia.org/wiki/NTFS) - For the amazing file system

## 📊 Performance

| Metric | Performance |
|--------|-------------|
| Initial Scan | 1,000,000+ files/second |
| Cached Access | 10,000,000+ files/second |
| Memory Usage | ~100MB base + ~10MB per 1M files |
| Threads | Auto-scales with CPU cores (up to 16) |
| Cache Size | Configurable, default 1M entries |

## 🚀 Key Features

- **Blazing Fast**: 1M+ files/second scanning using direct MFT access
- **Zero Latency**: In-memory caching of frequently accessed files
- **Multi-Threaded**: Parallel processing for maximum performance
- **Efficient**: Memory-mapped I/O for minimal overhead
- **Scalable**: Handles 100M+ files with ease
- **Privilege Separation**: Secure architecture with named pipe communication
- **Multi-Drive Support**: Seamlessly search across all NTFS volumes

## 🏗 Architecture

**High-Performance C++ Service with Python Bridge**: Optimized for speed and efficiency.

### Components

1. **Python MCP Bridge** (`fastsearch_mcp/`)
   - Lightweight Python interface to the native service
   - Handles JSON-RPC 2.0 protocol
   - Manages communication with Claude Desktop
   - **This is what Claude Desktop calls**

2. **C++ Windows Service** (`service/`) - **Core Engine**
   - High-performance C++17 service for NTFS MFT access
   - Memory-mapped I/O for maximum throughput
   - Multi-threaded processing (16+ threads)
   - Advanced caching with LRU eviction
   - Processes 1M+ files/second
   - Runs as a system service with elevated privileges

3. **Communication**
   - High-speed named pipe interface
   - Binary protocol for minimal overhead
   - Zero-copy data transfer where possible

## 🚀 Quick Start

### Prerequisites

- Windows 10/11 with NTFS volumes
- Python 3.8+ (for bridge)
- Visual Studio 2022 (for service compilation)
- Windows 10/11 SDK
- CMake 3.20+
- Claude Desktop with MCP support

### Installation

#### 1. Install from PyPI (Recommended)

```bash
pip install fastsearch-mcp
```

#### 2. Install from Source

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/fastsearch-mcp.git
   cd fastsearch-mcp
   ```

2. Install in development mode:

   ```bash
   pip install -e .[dev]
   ```

#### 3. Install the Windows Service

1. Build the service (requires Visual Studio 2022):

   ```powershell
   cd service
   mkdir build
   cd build
   cmake .. -G "Visual Studio 17 2022" -A x64
   cmake --build . --config Release
   ```

2. Install the service (admin privileges required):

   ```powershell
   # In an elevated PowerShell
   .\Release\FastSearchService.exe install
   Start-Service FastSearchService
   ```

## 🛠 Usage

### Starting the MCP Server

```bash
fastsearch-mcp
```

### Using with Claude Desktop

1. Install the DXT package:

   ```bash
   dxt install fastsearch-mcp
   ```

2. Restart Claude Desktop

3. Use the `@fastsearch` command in Claude Desktop to search files

### Example Search

```python
@fastsearch pattern: "*.py"
```

## 📚 Documentation

For detailed documentation, including API reference and development guides, see:

- [API Reference](docs/api.md)
- [Development Guide](docs/development.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [WizFile](https://www.antibody-software.com/) for demonstrating the power of direct MFT access
- The Claude team for the MCP protocol
- The Rust community for excellent systems programming tools

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/fastsearch-mcp.git
   cd fastsearch-mcp
   ```

2. Install Python dependencies:

   ```bash
   pip install -e .
   ```

3. Build and install the Windows service:

   ```bash
   cd service
   cargo build --release
   # Follow service installation instructions in service/README.md
   ```

4. Install the DXT package in Claude Desktop:

   ```bash
   dxt pack
   # Install the generated .dxt file in Claude Desktop
   ```

## 🛠 Usage

### Basic Search

Search for files using natural language:

```python
# Claude will automatically use FastSearch for file operations
Find all Python files modified in the last week that are larger than 1MB
```

### Advanced Search

Use specific search parameters:

```python
# Find large log files with specific patterns
Search for error logs from the last 24 hours:
- Path contains "logs"
- File extension is "log"
- Modified in the last 24 hours
- Size > 10MB
- Content contains "ERROR"
```

## 📚 Documentation

### MCP Methods

Documentation for all MCP methods is automatically generated from code:

```bash
python scripts/generate_docs.py
# View docs at docs/api.md
```

### DXT Integration

The DXT package includes LLM-friendly documentation that helps Claude understand how to use the MCP:

- **System Prompts**: Pre-defined prompts for Claude
- **Examples**: Common usage patterns
- **Parameter Validation**: Ensures correct usage
- **Error Handling**: Clear error messages

## 🔧 Development

### Directory Structure

```
fastsearch-mcp/
├── fastsearch_mcp/           # Python MCP implementation
│   ├── __init__.py
│   ├── mcp_server.py        # MCP server implementation
│   ├── decorators.py        # LLM documentation decorators
│   ├── ipc.py              # Windows named pipe client
│   └── __main__.py         # CLI entry point
├── service/                 # Rust Windows service
│   ├── src/
│   │   ├── main.rs        # Service entry point
│   │   ├── ntfs_reader.rs # Direct MFT access
│   │   └── lib.rs
│   └── Cargo.toml
├── tests/                   # Test suite
├── scripts/
│   └── generate_docs.py    # Documentation generator
├── dxt.yaml                # DXT package configuration
└── README.md               # This file
├── service/                   # FastSearch Service (elevated)
│   ├── src/
│   │   ├── main.rs           # Service entry point
│   │   ├── search_engine.rs  # Search logic (was mcp_server.rs)
│   │   ├── ntfs_reader.rs    # NTFS MFT reader
│   │   ├── web_api.rs        # Web API for frontend
│   │   └── lib.rs
│   └── Cargo.toml
├── shared/                    # Common types
│   ├── src/
│   │   ├── types.rs          # SearchRequest, SearchResponse, etc.
│   │   └── lib.rs
│   └── Cargo.toml
├── installer/                 # One-time UAC installation
├── frontend/                  # Web UI
└── Cargo.toml                # Workspace root
```

## Installation & Usage

### Prerequisites

- Windows 10/11 with NTFS file system
- Rust toolchain (for building from source)
- Administrator privileges (required for initial setup only)

### Manual Installation (Recommended for Development)

1. **Build the project** (from an elevated command prompt):

   ```powershell
   # Clone the repository
   git clone https://github.com/yourusername/fastsearch-mcp.git
   cd fastsearch-mcp
   
   # Build in release mode
   cargo build --release
   ```

2. **Install the Windows Service** (one-time setup with admin rights):

   ```powershell
   # Run as Administrator
   $servicePath = "D:\Dev\repos\fastsearch-mcp\target\release\fastsearch.exe"
   sc.exe create FastSearch binPath= "$servicePath --run-as-service" start= auto
   sc.exe description FastSearch "FastSearch MCP Service for lightning-fast file search using NTFS MFT"
   sc.exe start FastSearch
   ```

   > **Note**: Update `$servicePath` to match your actual path to the built `fastsearch.exe`

3. **Verify the service is running**:

   ```powershell
   sc.exe query FastSearch
   ```

### One-Click Installer (Coming Soon)

```powershell
# Download installer from GitHub releases
# Run installer as Administrator (one-time UAC prompt)
setup.exe
```

**What the installer will do:**

- Install FastSearch service with elevated privileges
- Register service for automatic startup
- Set up named pipe communication
- Configure the MCP bridge for Claude Desktop

### Claude Desktop Configuration

Add to your Claude Desktop configuration (typically in `settings.json` or via UI):

```json
{
  "mcpServers": {
    "fastsearch": {
      "command": "D:\\Dev\\repos\\fastsearch-mcp\\target\\release\\fastsearch-mcp-bridge.exe",
      "args": ["--service-pipe", "\\\\\\.\\pipe\\fastsearch-service"],
      "timeout": 30,
      "autoStart": true,
      "enabled": true,
      "description": "FastSearch MCP Bridge for lightning-fast file search using NTFS MFT"
    }
  }
}
```

## 🔒 Security

### Normal Operation (Privilege Separation)

- **Windows Service (Elevated)**
  - Runs automatically at system startup
  - Has direct NTFS MFT access
  - Listens on named pipe: `\\.\pipe\fastsearch-service`
  - No UI, runs in background

- **Bridge (User Mode)**
  - Started by Claude Desktop
  - Runs with normal user privileges
  - Forwards requests to elevated service
  - No UAC prompts during normal use

- **Performance**
  - Sub-100ms search response times
  - Minimal memory footprint
  - Efficient NTFS MFT scanning

## Development

## 🛠 Building from Source

### Prerequisites

- Rust 1.70+ (https://rustup.rs/)
- Windows 10/11 (x64)
- Python 3.8+ (for MCP bridge)

### Build Service (Rust)

```powershell
# Build the service
cd service
cargo build --release

# Install as Windows service (admin required)
sc.exe create FastSearch binPath= "%CD%\target\release\fastsearch-service.exe" start= auto
sc.exe start FastSearch
```

### Build MCP Bridge (Python)

```powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build DXT package
dxt build
```

### Verify Installation

```powershell
# Test direct search (service must be running)
.\target\release\fastsearch-service search "*.dxt" --drive all

# Test MCP bridge
python -m fastsearch_mcp --help
```

### Build Individual Components

```bash
# Build bridge only
cd bridge && cargo build --release

# Build service only  
cd service && cargo build --release

# Build shared types
cd shared && cargo build --release
```

### Test Architecture

```bash
# Test bridge standalone
./bridge/target/release/fastsearch-mcp-bridge.exe

# Test service (requires admin)
./service/target/release/fastsearch-service.exe
```

## Why This Architecture?

### Problem

- **NTFS MFT access requires elevated privileges**
- **Claude Desktop cannot run elevated MCP servers**
- **Users don't want UAC prompts during normal operation**

### Solution  

- **Service**: Runs elevated, handles NTFS access, installed once
- **Bridge**: Runs as user, handles MCP protocol, no elevation needed
- **Communication**: Named pipes for secure IPC

### Benefits

- ✅ **No UAC during normal use** - Only during installation
- ✅ **Secure privilege separation** - Service isolated from MCP protocol
- ✅ **Fast performance** - Direct NTFS MFT access
- ✅ **Seamless Claude integration** - Standard MCP server interface
- ✅ **Robust error handling** - Graceful degradation if service unavailable

## Features

- **Lightning-fast search** - Direct NTFS Master File Table reading
- **Multiple search types** - Exact, glob, regex, fuzzy matching
- **Real-time results** - Sub-100ms response times
- **Privilege separation** - Secure bridge/service architecture
- **Graceful fallback** - Helpful messages if service unavailable
- **REST API** - Web interface for integration with other applications

## Acknowledgments

- **WizFile**: For pioneering fast MFT-based search techniques
- **NTFS-3G**: For NTFS documentation and reference implementation
- **FastMCP**: For the MCP protocol specification

## License

MIT - See [LICENSE](LICENSE) for more information.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## Documentation

- [Project Plan](projects/FastSearch%20MCP%20Server%20-%20Project%20Plan.md)
- [MCP Ecosystem](MCP_ECOSYSTEM.md) - About MCP protocol and ecosystem
- [Web API](WEB_API.md) - REST API documentation for web and application integration

## Release Process

FastSearch MCP uses GitHub Actions for automated builds and releases. The release process is fully automated:

1. Create a version tag (e.g., `v1.0.0`)
2. Push the tag to trigger the release workflow
3. GitHub Actions builds for all platforms
4. Artifacts are uploaded to GitHub Releases

For detailed release instructions, see [RELEASING.md](RELEASING.md).

### Testing a Release Locally

Before creating a release, test the build process locally:

```powershell
# Run the test script
.\test-release.ps1
```

This will verify that all components build correctly and the installer is created successfully.

- **Web interface** - Optional frontend for direct access

## License

MIT - Sandra & Claudius
