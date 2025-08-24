"""
Command-line interface for the FastSearch MCP Bridge.

This module provides a command-line interface for starting and managing the
FastSearch MCP Bridge server.
"""

import argparse
import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .mcp_server import McpServer
from .exceptions import McpError
from .ipc import IpcError
from .logging_config import setup_logging, get_logger, log_system_info, struct_message

# Get logger
logger = get_logger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='FastSearch MCP 2.11.3 Server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Connection options
    connection_group = parser.add_argument_group('Connection Options')
    connection_group.add_argument(
        '--pipe',
        type=str,
        default=r'\\.\pipe\fastsearch-service',
        help='Named pipe for FastSearch service communication',
    )
    
    # Logging options
    logging_group = parser.add_argument_group('Logging Options')
    logging_group.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=os.environ.get('FASTSEARCH_LOG_LEVEL', 'INFO'),
        help='Set the logging level',
    )
    logging_group.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Path to log file (default: no file logging)',
    )
    logging_group.add_argument(
        '--log-max-size',
        type=int,
        default=10,  # MB
        help='Maximum log file size in MB before rotation',
    )
    logging_group.add_argument(
        '--log-backup-count',
        type=int,
        default=5,
        help='Number of backup log files to keep',
    )
    
    # Service options
    service_group = parser.add_argument_group('Service Options')
    service_group.add_argument(
        '--service-name',
        type=str,
        default='FastSearchMCP',
        help='Name of the Windows service',
    )
    
    # General options
    general_group = parser.add_argument_group('General Options')
    general_group.add_argument(
        '--version',
        action='store_true',
        help='Show version information and exit',
    )
    general_group.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (sets log level to DEBUG)',
    )
    
    return parser.parse_args()

async def shutdown(server: McpServer) -> None:
    """Shut down the server gracefully."""
    logger.info('Initiating graceful shutdown...')
    try:
        await server.stop()
        logger.info('Server stopped successfully')
    except Exception as e:
        logger.error('Error during shutdown: %s', e, exc_info=True)
    finally:
        # Ensure the event loop is stopped
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.stop()
        except Exception as e:
            logger.error('Error stopping event loop: %s', e)

def handle_signal(server: McpServer, signal_name: str) -> None:
    """Handle OS signals for graceful shutdown."""
    logger.info('Received %s signal. Initiating graceful shutdown...', signal_name)
    asyncio.create_task(shutdown(server))

def print_banner() -> None:
    """Print the application banner."""
    from . import __version__
    
    banner = f"""
    ╔══════════════════════════════════════════════════╗
    ║            FastSearch MCP Bridge v{__version__: <6}          ║
    ║    High-performance NTFS search and indexing     ║
    ╚══════════════════════════════════════════════════╝
    """
    print(banner)
    logger.debug("Debug mode enabled")

def setup_signal_handlers(server: McpServer) -> None:
    """Set up signal handlers for graceful shutdown."""
    try:
        loop = asyncio.get_event_loop()
        
        # Handle common termination signals
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: handle_signal(server, s.name)
                )
            except (ValueError, RuntimeError) as e:
                # Handle cases where signal can't be added (e.g., on Windows)
                logger.debug("Could not add signal handler for %s: %s", sig.name, e)
    except Exception as e:
        logger.warning("Failed to set up signal handlers: %s", e)

async def run_server(pipe_name: str) -> None:
    """Run the MCP server with the specified pipe name.
    
    Args:
        pipe_name: Name of the named pipe for communication
    """
    # Create and configure the server
    server = McpServer(pipe_name=pipe_name)
    
    try:
        # Start the server
        logger.info("Starting MCP server (pipe: %s)", pipe_name)
        await server.start()
        
        # Keep the server running until stopped
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.exception("Error in MCP server:")
        raise
    finally:
        # Ensure the server is properly stopped
        await server.stop()

def main() -> int:
    """Run the MCP server."""
    args = parse_args()
    
    # Handle version flag
    if args.version:
        from . import __version__
        print(f'FastSearch MCP Bridge v{__version__}')
        return 0
    
    # Set up logging
    log_level = 'DEBUG' if args.debug else args.log_level
    log_file = os.path.abspath(args.log_file) if args.log_file else None
    
    # If no log file specified, use a default location in the user's app data directory
    if log_file is None and os.name == 'nt':
        app_data = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
        log_dir = os.path.join(app_data, 'FastSearchMCP', 'Logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'fastsearch_mcp.log')
    
    # Configure logging
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        max_bytes=args.log_max_size * 1024 * 1024,  # Convert MB to bytes
        backup_count=args.log_backup_count,
        console=True
    )
    
    # Re-get logger with updated configuration
    global logger
    logger = get_logger(__name__)
    
    # Print banner
    if not args.log_file or args.debug:
        print_banner()
    
    # Log configuration
    logger.info("Starting FastSearch MCP Bridge")
    logger.debug("Command line arguments: %s", sys.argv)
    logger.debug("Effective configuration: %s", struct_message("", **{
        'pipe': args.pipe,
        'log_level': log_level,
        'log_file': log_file,
        'log_max_size': f"{args.log_max_size}MB",
        'log_backup_count': args.log_backup_count,
        'service_name': args.service_name,
    }))
    
    # Log system information
    log_system_info(logger)
    
    # Create and configure the server
    try:
        # Set up signal handlers
        loop = asyncio.get_event_loop()
        
        # Create a future to track server status
        server_task = loop.create_task(run_server(args.pipe))
        
        # Set up signal handlers for graceful shutdown
        def signal_handler():
            logger.info("Shutdown signal received, stopping server...")
            server_task.cancel()
            
        for signame in ('SIGINT', 'SIGTERM'):
            try:
                loop.add_signal_handler(
                    getattr(signal, signame),
                    signal_handler
                )
            except (ValueError, RuntimeError) as e:
                logger.warning("Could not add signal handler for %s: %s", signame, e)
        
        # Run the server until it's complete
        loop.run_until_complete(server_task)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        return 0
    except Exception as e:
        logger.exception("Unexpected error:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
