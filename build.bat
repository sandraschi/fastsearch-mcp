@echo off
setlocal enabledelayedexpansion

REM Set Visual Studio 2022 environment
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

REM Create build directory if it doesn't exist
if not exist "build" mkdir build

REM Configure with CMake
cmake -S service -B build -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release

REM Build the project
cmake --build build --config Release --target ALL_BUILD

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build completed successfully!
    echo The executable is in the build\bin\Release\ directory.
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
