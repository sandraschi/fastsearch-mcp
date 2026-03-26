# Minimal Windows Service Test
# This will help us determine if the issue is with our service code or Windows service setup

Write-Host "Creating minimal service test..." -ForegroundColor Yellow

# Check if we can create a simple service
$testServiceName = "TestService"
$testExePath = "C:\Windows\System32\notepad.exe"  # Use a known working executable

try {
    # Try to create a test service
    Write-Host "Creating test service..." -ForegroundColor Cyan
    $result = C:\Windows\System32\sc.exe create $testServiceName binPath= $testExePath start= demand
    Write-Host "Create result: $result" -ForegroundColor Green
    
    # Try to start it
    Write-Host "Starting test service..." -ForegroundColor Cyan
    $startResult = C:\Windows\System32\sc.exe start $testServiceName
    Write-Host "Start result: $startResult" -ForegroundColor Green
    
    # Check status
    $status = Get-Service $testServiceName -ErrorAction SilentlyContinue
    if ($status) {
        Write-Host "Test service status: $($status.Status)" -ForegroundColor Green
    }
    
    # Clean up
    Write-Host "Cleaning up test service..." -ForegroundColor Cyan
    C:\Windows\System32\sc.exe delete $testServiceName
    Write-Host "Test completed!" -ForegroundColor Green
    
} catch {
    Write-Host "Test failed: $($_.Exception.Message)" -ForegroundColor Red
}
