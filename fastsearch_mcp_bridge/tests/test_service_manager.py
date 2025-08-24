"""Tests for the Service Manager tool."""
import asyncio
import os
import sys
import time
import unittest
import unittest.mock
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastsearch_mcp.tools.service_manager import (
    ServiceManager, ServiceInfo, ServiceStatus, ServiceStartupType,
    ListServicesTool, GetServiceTool, StartServiceTool, StopServiceTool,
    RestartServiceTool, SetServiceStartupTypeTool, GetServiceLogsTool
)

class TestServiceInfo(unittest.TestCase):
    """Test the ServiceInfo class."""
    
    def test_to_dict(self):
        """Test converting ServiceInfo to dictionary."""
        service = ServiceInfo(
            name="TestService",
            display_name="Test Service",
            status=ServiceStatus.RUNNING,
            startup_type=ServiceStartupType.AUTOMATIC,
            binary_path="C:\\test.exe",
            description="A test service",
            pid=1234,
            exit_code=0,
            process_name="test.exe",
            username="SYSTEM",
            dependencies=["RPCSS", "Dnscache"],
            delayed_start=True,
            error_control="NORMAL",
            load_order_group="",
            service_type="WIN32_OWN_PROCESS",
            tag_id=1
        )
        
        result = service.to_dict()
        
        self.assertEqual(result["name"], "TestService")
        self.assertEqual(result["display_name"], "Test Service")
        self.assertEqual(result["status"], "RUNNING")
        self.assertEqual(result["startup_type"], "AUTOMATIC")
        self.assertEqual(result["binary_path"], "C:\\test.exe")
        self.assertEqual(result["description"], "A test service")
        self.assertEqual(result["pid"], 1234)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["process_name"], "test.exe")
        self.assertEqual(result["username"], "SYSTEM")
        self.assertEqual(result["dependencies"], ["RPCSS", "Dnscache"])
        self.assertEqual(result["delayed_start"], True)
        self.assertEqual(result["error_control"], "NORMAL")
        self.assertEqual(result["load_order_group"], "")
        self.assertEqual(result["service_type"], "WIN32_OWN_PROCESS")
        self.assertEqual(result["tag_id"], 1)

class TestServiceManager(unittest.TestCase):
    """Test the ServiceManager class."""
    
    @patch('win32service.OpenSCManager')
    @patch('win32service.EnumServicesStatusEx')
    @patch('win32service.CloseServiceHandle')
    def test_get_services(self, mock_close, mock_enum, mock_scm):
        """Test getting all services."""
        # Mock service handles
        scm_handle = MagicMock()
        mock_scm.return_value = scm_handle
        
        # Mock service enumeration
        mock_enum.return_value = [
            ("TestService1", "Test Service 1", 0x00000010),  # SERVICE_RUNNING
            ("TestService2", "Test Service 2", 0x00000020),  # SERVICE_STOPPED
        ]
        
        # Mock ServiceInfo.from_win32_service
        with patch.object(ServiceInfo, 'from_win32_service') as mock_from_win32:
            mock_from_win32.side_effect = [
                ServiceInfo("TestService1", "Test Service 1", ServiceStatus.RUNNING, ServiceStartupType.AUTOMATIC, "C:\\test1.exe"),
                ServiceInfo("TestService2", "Test Service 2", ServiceStatus.STOPPED, ServiceStartupType.MANUAL, "C:\\test2.exe"),
            ]
            
            services = ServiceManager.get_services()
            
            self.assertEqual(len(services), 2)
            self.assertEqual(services[0].name, "TestService1")
            self.assertEqual(services[1].name, "TestService2")
            
            # Verify the service handles were closed
            mock_close.assert_called()
    
    @patch('win32serviceutil.StartService')
    def test_start_service(self, mock_start_service):
        """Test starting a service."""
        # Mock the service to be returned by get_service
        with patch.object(ServiceManager, 'get_service') as mock_get_service:
            mock_get_service.return_value = ServiceInfo(
                "TestService", "Test Service", 
                ServiceStatus.STOPPED, 
                ServiceStartupType.MANUAL,
                "C:\\test.exe"
            )
            
            # Call the method
            result = ServiceManager.start_service("TestService")
            
            # Verify the result
            self.assertTrue(result["success"])
            self.assertIn("Successfully started service 'TestService'", result["message"])
            
            # Verify the service was started
            mock_start_service.assert_called_once_with("TestService", "")
    
    @patch('win32serviceutil.StopService')
    def test_stop_service(self, mock_stop_service):
        """Test stopping a service."""
        # Mock the service to be returned by get_service
        with patch.object(ServiceManager, 'get_service') as mock_get_service:
            mock_get_service.return_value = ServiceInfo(
                "TestService", "Test Service", 
                ServiceStatus.RUNNING, 
                ServiceStartupType.MANUAL,
                "C:\\test.exe"
            )
            
            # Call the method
            result = ServiceManager.stop_service("TestService")
            
            # Verify the result
            self.assertTrue(result["success"])
            self.assertIn("Successfully stopped service 'TestService'", result["message"])
            
            # Verify the service was stopped
            mock_stop_service.assert_called_once_with("TestService")

class TestServiceTools(unittest.IsolatedAsyncioTestCase):
    """Test the service management tools."""
    
    async def test_list_services_tool(self):
        """Test the ListServicesTool."""
        # Create a mock service
        mock_service = ServiceInfo(
            "TestService", "Test Service", 
            ServiceStatus.RUNNING, 
            ServiceStartupType.AUTOMATIC,
            "C:\\test.exe"
        )
        
        # Patch the ServiceManager.get_services method
        with patch.object(ServiceManager, 'get_services') as mock_get_services:
            mock_get_services.return_value = [mock_service]
            
            # Create and execute the tool
            tool = ListServicesTool()
            result = await tool.execute(status="running", include_details=True)
            
            # Verify the result
            self.assertTrue(result["success"])
            self.assertEqual(len(result["services"]), 1)
            self.assertEqual(result["services"][0]["name"], "TestService")
            self.assertEqual(result["services"][0]["status"], "RUNNING")
    
    async def test_get_service_tool(self):
        """Test the GetServiceTool."""
        # Create a mock service
        mock_service = ServiceInfo(
            "TestService", "Test Service", 
            ServiceStatus.RUNNING, 
            ServiceStartupType.AUTOMATIC,
            "C:\\test.exe"
        )
        
        # Patch the ServiceManager.get_service method
        with patch.object(ServiceManager, 'get_service') as mock_get_service:
            mock_get_service.return_value = mock_service
            
            # Create and execute the tool
            tool = GetServiceTool()
            result = await tool.execute(service_name="TestService")
            
            # Verify the result
            self.assertTrue(result["success"])
            self.assertEqual(result["service"]["name"], "TestService")
            self.assertEqual(result["service"]["status"], "RUNNING")
    
    async def test_start_service_tool(self):
        """Test the StartServiceTool."""
        # Patch the ServiceManager.start_service method
        with patch.object(ServiceManager, 'start_service') as mock_start_service:
            mock_start_service.return_value = {
                "success": True,
                "message": "Successfully started service 'TestService'",
                "service": "TestService",
                "status": "RUNNING"
            }
            
            # Create and execute the tool
            tool = StartServiceTool()
            result = await tool.execute(service_name="TestService", timeout=30)
            
            # Verify the result
            self.assertTrue(result["success"])
            self.assertIn("Successfully started service 'TestService'", result["message"])
            
            # Verify the service was started
            mock_start_service.assert_called_once_with("TestService", [], 30)
    
    async def test_stop_service_tool(self):
        """Test the StopServiceTool."""
        # Patch the ServiceManager.stop_service method
        with patch.object(ServiceManager, 'stop_service') as mock_stop_service:
            mock_stop_service.return_value = {
                "success": True,
                "message": "Successfully stopped service 'TestService'",
                "service": "TestService",
                "status": "STOPPED"
            }
            
            # Create and execute the tool
            tool = StopServiceTool()
            result = await tool.execute(service_name="TestService", timeout=30)
            
            # Verify the result
            self.assertTrue(result["success"])
            self.assertIn("Successfully stopped service 'TestService'", result["message"])
            
            # Verify the service was stopped
            mock_stop_service.assert_called_once_with("TestService", 30)
    
    async def test_restart_service_tool(self):
        """Test the RestartServiceTool."""
        # Patch the ServiceManager.restart_service method
        with patch.object(ServiceManager, 'restart_service') as mock_restart_service:
            mock_restart_service.return_value = {
                "success": True,
                "message": "Successfully restarted service 'TestService'",
                "service": "TestService",
                "status": "RUNNING"
            }
            
            # Create and execute the tool
            tool = RestartServiceTool()
            result = await tool.execute(service_name="TestService", timeout=60)
            
            # Verify the result
            self.assertTrue(result["success"])
            self.assertIn("Successfully restarted service 'TestService'", result["message"])
            
            # Verify the service was restarted
            mock_restart_service.assert_called_once_with("TestService", 60)
    
    async def test_set_service_startup_type_tool(self):
        """Test the SetServiceStartupTypeTool."""
        # Patch the ServiceManager.set_startup_type method
        with patch.object(ServiceManager, 'set_startup_type') as mock_set_startup_type:
            mock_set_startup_type.return_value = {
                "success": True,
                "message": "Set startup type for service 'TestService' to AUTOMATIC",
                "service": "TestService",
                "startup_type": "AUTOMATIC"
            }
            
            # Create and execute the tool
            tool = SetServiceStartupTypeTool()
            result = await tool.execute(service_name="TestService", startup_type="automatic")
            
            # Verify the result
            self.assertTrue(result["success"])
            self.assertIn("Set startup type for service 'TestService' to AUTOMATIC", result["message"])
            
            # Verify the startup type was set
            mock_set_startup_type.assert_called_once_with("TestService", "automatic")

if __name__ == "__main__":
    unittest.main()
