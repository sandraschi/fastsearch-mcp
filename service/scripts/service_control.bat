@echo off
setlocal enabledelayedexpansion

:: Service Control Script for FastSearch MCP
:: Usage: service_control.bat [command]
:: Commands:
::   start    - Start the service
::   stop     - Stop the service
::   restart  - Restart the service
::   status   - Show service status
::   install  - Install the service
::   uninstall - Uninstall the service
::   help     - Show this help message

set "SERVICE_NAME=FastSearchService"
set "SERVICE_DISPLAY=FastSearch MCP Service"
set "SERVICE_PATH=%~dp0..\build\Release\FastSearchService.exe"

if "%1"=="" (
    echo Error: No command specified
    call :show_help
    exit /b 1
)

if "%1"=="help" (
    call :show_help
    exit /b 0
)

:: Check if running with admin rights
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: This script requires administrator privileges.
    echo Please run as Administrator.
    exit /b 1
)

:: Process commands
if "%1"=="start" (
    echo Starting %SERVICE_DISPLAY%...
    net start "%SERVICE_NAME%"
) else if "%1"=="stop" (
    echo Stopping %SERVICE_DISPLAY%...
    net stop "%SERVICE_NAME%"
) else if "%1"=="restart" (
    call "%~f0" stop
    timeout /t 2 >nul
    call "%~f0" start
) else if "%1"=="status" (
    sc query "%SERVICE_NAME%"
) else if "%1"=="install" (
    echo Installing %SERVICE_DISPLAY%...
    if not exist "%SERVICE_PATH%" (
        echo Error: Service executable not found at %SERVICE_PATH%
        exit /b 1
    )
    sc create "%SERVICE_NAME%" binPath= "\"%SERVICE_PATH%\"" DisplayName= "%SERVICE_DISPLAY%" start= auto
    sc description "%SERVICE_NAME%" "Provides high-performance NTFS file search capabilities"
    sc failure "%SERVICE_NAME%" reset= 86400 actions= restart/60000/restart/60000/restart/60000
    echo Service installed successfully.
    echo Starting service...
    net start "%SERVICE_NAME%"
) else if "%1"=="uninstall" (
    echo Stopping service...
    net stop "%SERVICE_NAME%" 2>nul
    echo Uninstalling %SERVICE_DISPLAY%...
    sc delete "%SERVICE_NAME%"
    echo Service uninstalled successfully.
) else (
    echo Error: Unknown command '%1'
    call :show_help
    exit /b 1
)

exit /b 0

:show_help
echo.
echo FastSearch MCP Service Control
echo ===========================
echo.
echo Usage: service_control.bat ^<command^>
echo.
echo Commands:
echo   start     - Start the service
echo   stop      - Stop the service
echo   restart   - Restart the service
echo   status    - Show service status
echo   install   - Install the service
echo   uninstall - Uninstall the service
echo   help      - Show this help message
echo.
exit /b 0
