"""
Integration tests for the service manager.
"""

from unittest.mock import MagicMock, patch

import pytest

from fastsearch_mcp.tools.service_manager import ServiceManager, ServiceStartupType


class TestServiceManagerIntegration:
    """Integration tests for the ServiceManager class."""

    @pytest.fixture
    def service_manager(self):
        """Create a ServiceManager instance for testing."""
        return ServiceManager()

    @pytest.mark.skip(reason="Requires Windows service access")
    def test_get_services(self, service_manager):
        """Test getting a list of services."""
        services = service_manager.get_services()
        assert isinstance(services, list)

        if services:  # If there are services
            service = services[0]
            assert hasattr(service, "name")
            assert hasattr(service, "display_name")
            assert hasattr(service, "status")

    @patch("fastsearch_mcp.tools.service_manager.win32serviceutil.QueryServiceStatus")
    @patch("fastsearch_mcp.tools.service_manager.win32serviceutil.OpenService")
    @patch("fastsearch_mcp.tools.service_manager.win32serviceutil.EnumServicesStatus")
    def test_get_services_mocked(self, mock_enum_services, mock_open_service, mock_query_status, service_manager):
        """Test getting services with mocked Windows API."""
        # Setup mocks
        mock_enum_services.return_value = [
            ("MockService1", "Mock Service 1", 0),
            ("MockService2", "Mock Service 2", 0),
        ]

        mock_service = MagicMock()
        mock_service.QueryServiceConfig.return_value = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
        mock_open_service.return_value = mock_service

        mock_query_status.return_value = (1, 0, 0, 0, 0, 0, 0)

        # Call the method
        services = service_manager.get_services()

        # Assertions
        assert len(services) == 2
        assert services[0].name == "MockService1"
        assert services[1].name == "MockService2"

    @patch("fastsearch_mcp.tools.service_manager.win32serviceutil.StartService")
    @patch("fastsearch_mcp.tools.service_manager.win32serviceutil.OpenService")
    def test_start_service(self, mock_open_service, mock_start_service, service_manager):
        """Test starting a service with mocked Windows API."""
        # Setup mocks
        mock_service = MagicMock()
        mock_open_service.return_value = mock_service
        mock_start_service.return_value = None

        # Call the method
        result = service_manager.start_service("MockService")

        # Assertions
        assert "status" in result
        assert result["status"] == "success" or "pending" in result["status"].lower()
        mock_start_service.assert_called_once()

    @patch("fastsearch_mcp.tools.service_manager.win32serviceutil.ControlService")
    @patch("fastsearch_mcp.tools.service_manager.win32serviceutil.OpenService")
    def test_stop_service(self, mock_open_service, mock_control_service, service_manager):
        """Test stopping a service with mocked Windows API."""
        # Setup mocks
        mock_service = MagicMock()
        mock_open_service.return_value = mock_service
        mock_control_service.return_value = (1, 0, 0, 0, 0, 0, 0)

        # Call the method
        result = service_manager.stop_service("MockService")

        # Assertions
        assert "status" in result
        assert result["status"] == "success" or "pending" in result["status"].lower()
        mock_control_service.assert_called_once_with(mock_service, 1)  # 1 = SERVICE_CONTROL_STOP

    @patch("fastsearch_mcp.tools.service_manager.win32serviceutil.ChangeServiceConfig")
    @patch("fastsearch_mcp.tools.service_manager.win32serviceutil.OpenService")
    def test_set_startup_type(self, mock_open_service, mock_change_config, service_manager):
        """Test setting the startup type of a service."""
        # Setup mocks
        mock_service = MagicMock()
        mock_open_service.return_value = mock_service
        mock_change_config.return_value = None

        # Test setting to AUTOMATIC
        result = service_manager.set_startup_type("MockService", ServiceStartupType.AUTOMATIC)
        assert result["status"] == "success"

        # Test setting to DISABLED
        result = service_manager.set_startup_type("MockService", ServiceStartupType.DISABLED)
        assert result["status"] == "success"
