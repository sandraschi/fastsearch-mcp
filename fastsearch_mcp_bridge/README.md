# FastSearch MCP Bridge (Python)

A FastMCP 2.10 compliant server implementation for FastSearch, written in Python.

## Features

- FastMCP 2.10 compliant server
- Easy integration with FastSearch backend
- Cross-platform support (Windows, Linux, macOS)
- Simple installation and configuration

## Installation

1. Ensure you have Python 3.8 or higher installed
2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Usage

### Running the MCP Bridge

```bash
fastsearch-mcp-bridge
```

### Configuration

Create a `.env` file in the project root with the following variables:

```env
# Path to the FastSearch service pipe
FASTSEARCH_PIPE=\\.\pipe\fastsearch-service

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

## Development

### Setting up the development environment

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Running tests

```bash
pytest
```

### Code formatting

```bash
black .
isort .
```

## License

MIT
