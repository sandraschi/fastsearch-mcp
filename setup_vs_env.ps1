# Try to find and run vcvarsall.bat
$vcvarsallPaths = @(
    "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
)

$vcvarsallPath = $vcvarsallPaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $vcvarsallPath) {
    Write-Error "Could not find vcvars64.bat. Make sure Visual Studio is installed with C++ workload."
    exit 1
}

Write-Host "Found Visual Studio at: $vcvarsallPath"

# Create a temporary batch file to set up the environment and run the build
$tempBatFile = [System.IO.Path]::GetTempFileName() + ".bat"
$buildCmd = @"
@echo off
call "$vcvarsallPath"
cd /d "$PWD"
cl /EHsc test_build.cpp
if %ERRORLEVEL% EQU 0 (
    echo Build successful! Running test_build.exe...
    .\test_build.exe
) else (
    echo Build failed with error code %ERRORLEVEL%
)
pause
exit /b %ERRORLEVEL%
"@

$buildCmd | Out-File -FilePath $tempBatFile -Encoding ASCII

# Run the batch file
Write-Host "Running build with Visual Studio environment..."
Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$tempBatFile`"" -NoNewWindow -Wait

# Clean up
Remove-Item -Path $tempBatFile -Force
