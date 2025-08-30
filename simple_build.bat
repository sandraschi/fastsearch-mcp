@echo off
setlocal enabledelayedexpansion

REM Create build directory if it doesn't exist
if not exist "build" mkdir build

REM Build the project using MSBuild
msbuild service\CMakeLists.txt /p:Configuration=Release /p:Platform=x64 /p:VisualStudioVersion=17.0

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build completed successfully!
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
