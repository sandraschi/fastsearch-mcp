@echo off
setlocal enabledelayedexpansion

REM Try to find vcvarsall.bat
set VCVARSALL="C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

if not exist %VCVARSALL% (
    set VCVARSALL="C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
)

if not exist %VCVARSALL% (
    echo Could not find Visual Studio 2022 installation.
    echo Please ensure Visual Studio 2022 with C++ workload is installed.
    pause
    exit /b 1
)

echo Setting up Visual Studio environment...
call %VCVARSALL%

REM Create build directory if it doesn't exist
if not exist "build" mkdir build

REM Configure with CMake
echo Configuring project...
cmake -S service -B build -G "Visual Studio 17 2022" -A x64

if %ERRORLEVEL% NEQ 0 (
    echo CMake configuration failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

REM Build the project
echo Building project...
cmake --build build --config Release

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build completed successfully!
    echo The executable is in the build\bin\Release\ directory.
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
)

pause
