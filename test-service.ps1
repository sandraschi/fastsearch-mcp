# Test script to run the service executable and capture errors
Write-Host "Testing FastSearch Service Executable..." -ForegroundColor Yellow

# Try to run the service executable and capture any output
try {
    $process = Start-Process -FilePath ".\service\build\bin\Release\FastSearchServiceNew.exe" -ArgumentList "" -PassThru -Wait -NoNewWindow
    Write-Host "Process exited with code: $($process.ExitCode)" -ForegroundColor Cyan
}
catch {
    Write-Host "Error running service: $($_.Exception.Message)" -ForegroundColor Red
}

# Check if there are any missing DLLs
Write-Host "`nChecking for missing dependencies..." -ForegroundColor Yellow
$deps = Get-ChildItem ".\service\build\bin\Release\" -Filter "*.dll"
if ($deps) {
    Write-Host "Found DLLs:" -ForegroundColor Green
    $deps | ForEach-Object { Write-Host "  $($_.Name)" -ForegroundColor Cyan }
} else {
    Write-Host "No DLLs found in service directory" -ForegroundColor Yellow
}

# Check if the executable exists and its properties
$exePath = ".\service\build\bin\Release\FastSearchServiceNew.exe"
if (Test-Path $exePath) {
    $fileInfo = Get-Item $exePath
    Write-Host "`nExecutable info:" -ForegroundColor Green
    Write-Host "  Size: $($fileInfo.Length) bytes" -ForegroundColor Cyan
    Write-Host "  Created: $($fileInfo.CreationTime)" -ForegroundColor Cyan
    Write-Host "  Modified: $($fileInfo.LastWriteTime)" -ForegroundColor Cyan
} else {
    Write-Host "Executable not found at: $exePath" -ForegroundColor Red
}
