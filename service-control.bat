@echo off
REM FastSearch MCP Service Control Script
REM This script provides easy access to service management commands

echo FastSearch MCP Service Control
echo =============================
echo.

:menu
echo Select an option:
echo 1. Install Service
echo 2. Uninstall Service
echo 3. Start Service
echo 4. Stop Service
echo 5. Service Status
echo 6. Diagnose Issues
echo 7. Test Service Startup
echo 8. Exit
echo.

set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto uninstall
if "%choice%"=="3" goto start
if "%choice%"=="4" goto stop
if "%choice%"=="5" goto status
if "%choice%"=="6" goto diagnose
if "%choice%"=="7" goto test
if "%choice%"=="8" goto exit
echo Invalid choice. Please try again.
echo.
goto menu

:install
echo.
echo Installing FastSearch MCP Service...
powershell -ExecutionPolicy Bypass -File "%~dp0install-service.ps1" install
echo.
goto menu

:uninstall
echo.
echo Uninstalling FastSearch MCP Service...
powershell -ExecutionPolicy Bypass -File "%~dp0install-service.ps1" uninstall
echo.
goto menu

:start
echo.
echo Starting FastSearch MCP Service...
powershell -ExecutionPolicy Bypass -File "%~dp0install-service.ps1" start
echo.
goto menu

:stop
echo.
echo Stopping FastSearch MCP Service...
powershell -ExecutionPolicy Bypass -File "%~dp0install-service.ps1" stop
echo.
goto menu

:status
echo.
echo Checking FastSearch MCP Service Status...
powershell -ExecutionPolicy Bypass -File "%~dp0install-service.ps1" status
echo.
goto menu

:diagnose
echo.
echo Diagnosing FastSearch MCP Service Issues...
powershell -ExecutionPolicy Bypass -File "%~dp0install-service.ps1" diagnose
echo.
goto menu

:test
echo.
echo Testing FastSearch MCP Service Startup...
powershell -ExecutionPolicy Bypass -File "%~dp0test-service-startup.ps1"
echo.
goto menu

:exit
echo.
echo Goodbye!
pause
exit
