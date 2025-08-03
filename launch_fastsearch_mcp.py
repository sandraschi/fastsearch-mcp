#!/usr/bin/env python3
"""
FastSearch MCP Launcher
A simple launcher for the FastSearch MCP service.
"""
import sys
import os
import subprocess
import ctypes
import platform

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    print("FastSearch MCP Launcher")
    print("======================")
    
    # Check if running as admin (required for service operations)
    if not is_admin():
        print("This application requires administrator privileges.")
        print("Please right-click and select 'Run as administrator'.")
        input("Press Enter to exit...")
        return 1
    
    # Get the path to the Python interpreter in the packaged environment
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_dir = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set up environment
    os.environ["FASTSEARCH_MCP_HOME"] = base_dir
    
    try:
        # Import and run the MCP server
        from fastsearch_mcp.mcp_server import main as mcp_main
        print("Starting FastSearch MCP service...")
        mcp_main()
    except ImportError as e:
        print(f"Error: Failed to import MCP server: {e}")
        print("Please ensure all dependencies are installed.")
        return 1
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
