@echo off
setlocal enabledelayedexpansion

:: Check if Visual Studio environment is set up
where cl >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Visual Studio environment not found. Please run this script from a Visual Studio Developer Command Prompt.
    echo Or run: "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
    pause
    exit /b 1
)

:: Create build directory
if not exist "build" mkdir build
cd build

:: Configure with CMake
cmake -G "Visual Studio 17 2022" -A x64 ..
if %ERRORLEVEL% neq 0 (
    echo CMake configuration failed
    pause
    exit /b 1
)

:: Build the project
cmake --build . --config Release
if %ERRORLEVEL% neq 0 (
    echo Build failed
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo The service executable is in: %CD%\bin\Release\FastSearchService.exe
echo.
echo To install the service, run as Administrator:
echo   FastSearchService.exe install
echo.
pause
