# FastSearch MCP Service

This directory contains the FastSearch MCP Windows Service implementation.

## Prerequisites

- Python 3.8+
- Windows 10/11 or Windows Server 2016+
- Administrator privileges for service installation

## Building the Service

1. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

2. Build the service executable:
   ```
   .\build_service.ps1
   ```
   This will create a `dist` directory containing the service executable and required files.

## Installing the Service

To install the service (run as Administrator):
```
.\install_service.ps1 -Action install
```

## Managing the Service

- Start the service:
  ```
  .\install_service.ps1 -Action start
  ```

- Stop the service:
  ```
  .\install_service.ps1 -Action stop
  ```

- Uninstall the service:
  ```
  .\install_service.ps1 -Action uninstall
  ```

## Service Details

- **Service Name**: FastSearchMCP
- **Display Name**: FastSearch MCP Service
- **Description**: Provides fast file search capabilities using MFT
- **Pipe Name**: `\\.\pipe\fastsearch-service`

## Troubleshooting

- If the service fails to start, check the Windows Event Viewer for error messages.
- Ensure the service account has appropriate permissions to access the MFT and file system.
- The service requires elevated privileges to access the MFT directly.

## Development

- The main service implementation is in `src/fastsearch_service_python/service.py`
- After making changes, rebuild the service using `build_service.ps1`
- Restart the service to apply changes

## License

[Your License Here]
