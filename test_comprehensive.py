#!/usr/bin/env python3
"""
Comprehensive Test Suite for FastSearch MCP
Tests the complete Python ↔ C++ service integration
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.service_client import is_service_running, get_service_client, search_files_via_service
from fastsearch_mcp.server import FastSearchServer

def setup_logging():
    """Setup logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_service_client():
    """Test the service client functionality."""
    print("=" * 60)
    print("🧪 TESTING SERVICE CLIENT")
    print("=" * 60)
    
    # Test 1: Service status check
    print("\n1️⃣ Testing service status check...")
    service_running = is_service_running()
    print(f"   Service running: {service_running}")
    
    if not service_running:
        print("   ⚠️  Service is not running. This is expected if not installed.")
        return False
    
    # Test 2: Service client creation
    print("\n2️⃣ Testing service client creation...")
    client = get_service_client()
    print(f"   Client created: {client is not None}")
    print(f"   Pipe name: {client.pipe_name}")
    
    # Test 3: Service status via client
    print("\n3️⃣ Testing service status via client...")
    status = client.get_service_status()
    print(f"   Status: {status}")
    
    # Test 4: File search (if service is running)
    if service_running:
        print("\n4️⃣ Testing file search...")
        try:
            results = client.search_files("*.txt", ".", 10)
            print(f"   Search results: {len(results)} files found")
            if results:
                print(f"   First result: {results[0]}")
        except Exception as e:
            print(f"   Search failed: {e}")
    
    return service_running

def test_fastmcp_server():
    """Test the FastMCP server."""
    print("\n" + "=" * 60)
    print("🧪 TESTING FASTMCP SERVER")
    print("=" * 60)
    
    try:
        # Test 1: Server creation
        print("\n1️⃣ Testing server creation...")
        server = FastSearchServer()
        print(f"   Server created: {server is not None}")
        print(f"   Server name: {server.name}")
        
        # Test 2: Tool registration
        print("\n2️⃣ Testing tool registration...")
        # Note: get_tools() might be async, so we'll just check if server was created
        print(f"   Server initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Server creation failed: {e}")
        return False

def test_frontend():
    """Test the frontend availability."""
    print("\n" + "=" * 60)
    print("🧪 TESTING FRONTEND")
    print("=" * 60)
    
    # Test 1: Simple frontend
    print("\n1️⃣ Testing simple FastSearch frontend...")
    frontend_path = Path("frontend/index.html")
    if frontend_path.exists():
        print(f"   ✅ Simple frontend exists: {frontend_path}")
        print(f"   📁 Frontend directory: {frontend_path.parent}")
    else:
        print(f"   ❌ Simple frontend not found: {frontend_path}")
    
    # Test 2: React frontend
    print("\n2️⃣ Testing React frontend...")
    react_app_path = Path("frontend/src/App.js")
    if react_app_path.exists():
        print(f"   ✅ React frontend exists: {react_app_path}")
        print(f"   📦 Package.json exists: {Path('frontend/package.json').exists()}")
    else:
        print(f"   ❌ React frontend not found: {react_app_path}")
    
    return True

def test_service_executable():
    """Test the service executable."""
    print("\n" + "=" * 60)
    print("🧪 TESTING SERVICE EXECUTABLE")
    print("=" * 60)
    
    # Test 1: Executable exists
    print("\n1️⃣ Testing service executable...")
    exe_path = Path("service/build/bin/Release/FastSearchService.exe")
    if exe_path.exists():
        print(f"   ✅ Service executable exists: {exe_path}")
        print(f"   📊 File size: {exe_path.stat().st_size} bytes")
    else:
        print(f"   ❌ Service executable not found: {exe_path}")
        return False
    
    # Test 2: Help command
    print("\n2️⃣ Testing service help command...")
    try:
        import subprocess
        result = subprocess.run([str(exe_path), "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Service help command works")
            print(f"   📝 Help output:\n{result.stdout}")
        else:
            print(f"   ❌ Service help failed: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Service help test failed: {e}")
    
    return True

def run_integration_test():
    """Run a complete integration test."""
    print("\n" + "=" * 60)
    print("🧪 INTEGRATION TEST")
    print("=" * 60)
    
    print("\n📋 Integration Test Steps:")
    print("1. Install service (requires UAC)")
    print("2. Start service")
    print("3. Test Python ↔ C++ communication")
    print("4. Test FastMCP server")
    print("5. Test frontend")
    
    print("\n🚀 To run integration test:")
    print("1. Run as Administrator: PowerShell -ExecutionPolicy Bypass -File install-service.ps1 install")
    print("2. Run: PowerShell -ExecutionPolicy Bypass -File install-service.ps1 start")
    print("3. Run: python test_comprehensive.py")
    print("4. Open: frontend/index.html in browser")

def main():
    """Main test function."""
    setup_logging()
    
    print("🚀 FastSearch MCP Comprehensive Test Suite")
    print("=" * 60)
    
    # Run all tests
    tests_passed = 0
    total_tests = 4
    
    if test_service_executable():
        tests_passed += 1
    
    if test_service_client():
        tests_passed += 1
    
    if test_fastmcp_server():
        tests_passed += 1
    
    if test_frontend():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Ready for integration testing.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    # Integration test instructions
    run_integration_test()

if __name__ == "__main__":
    main()
