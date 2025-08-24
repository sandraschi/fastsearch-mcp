# FastSearch MCP Bridge

A Python implementation of the MCP 2.11.3 protocol for FastSearch NTFS search service, providing a powerful set of tools for managing the FastSearch service and monitoring NTFS health.

## Features

- **Service Management**: Start, stop, restart, and monitor Windows services
- **Service Monitoring**: Get detailed information about running services
- **Event Logs**: View and filter service-related event logs
- **Startup Configuration**: Configure service startup types (Automatic, Manual, Disabled)
- **NTFS Health Checks**: Comprehensive NTFS volume monitoring and diagnostics
- **Self-Documenting**: Built-in help system for discovering available tools
- **Extensible**: Easy to add new tools and functionality
- **Simple Installation**: Quick setup and configuration

## Installation

1. Ensure you have Python 3.8 or higher installed

2. Install the package in development mode:

   ```bash
   pip install -e .
   ```

## Service Manager Tool

The Service Manager tool provides comprehensive management capabilities for Windows services, including:

### Key Features

- **List Services**: View all services with filtering by status, startup type, and name
- **Service Control**: Start, stop, and restart services
- **Service Configuration**: View and modify service startup types
- **Service Monitoring**: Get detailed information about specific services
- **Event Logs**: Access service-related event logs with filtering options

### Available Commands

1. **List Services**

   ```json
   {
     "tool": "list_services",
     "status": "running",  // Optional: all, running, stopped, start_pending, etc.
     "startup_type": "automatic",  // Optional: automatic, manual, disabled, boot, system
     "search": "search term",  // Optional: filter by service name or display name
     "include_details": true  // Optional: include full service details (default: true)
   }
   ```

2. **Get Service Information**

   ```json
   {
     "tool": "get_service",
     "service_name": "ServiceName"
   }
   ```

3. **Start a Service**

   ```json
   {
     "tool": "start_service",
     "service_name": "ServiceName",
     "args": [],  // Optional: service arguments
     "timeout": 30  // Optional: timeout in seconds (default: 30)
   }
   ```

4. **Stop a Service**

   ```json
   {
     "tool": "stop_service",
     "service_name": "ServiceName",
     "timeout": 30  // Optional: timeout in seconds (default: 30)
   }
   ```

5. **Restart a Service**

   ```json
   {
     "tool": "restart_service",
     "service_name": "ServiceName",
     "timeout": 60  // Optional: timeout in seconds (default: 60)
   }
   ```

6. **Set Service Startup Type**

   ```json
   {
     "tool": "set_service_startup_type",
     "service_name": "ServiceName",
     "startup_type": "automatic"  // automatic, manual, disabled, boot, system
   }
   ```

7. **Get Service Logs**

   ```json
   {
     "tool": "get_service_logs",
     "service_name": "ServiceName",
     "log_type": "system",  // Optional: system, application, security, etc.
     "source": "ServiceName",  // Optional: event source (defaults to service name)
     "last": "1h",  // Optional: time filter (e.g., "10m", "2h", "1d")
     "limit": 50,  // Optional: maximum number of log entries (default: 50)
     "event_level": "all"  // Optional: all, critical, error, warning, information, verbose
   }
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
