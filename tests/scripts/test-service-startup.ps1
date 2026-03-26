# Test the service executable with verbose output
Write-Host "Testing service executable startup..." -ForegroundColor Yellow

# Try to run the service executable and capture any output
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = ".\service\build\bin\Release\FastSearchServiceNew.exe"
$processInfo.UseShellExecute = $false
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.CreateNoWindow = $true

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $processInfo

try {
    $process.Start()
    $output = $process.StandardOutput.ReadToEnd()
    $errorOutput = $process.StandardError.ReadToEnd()
    $process.WaitForExit(5000)  # Wait 5 seconds
    
    Write-Host "Exit Code: $($process.ExitCode)" -ForegroundColor Cyan
    if ($output) {
        Write-Host "Output: $output" -ForegroundColor Green
    }
    if ($errorOutput) {
        Write-Host "Error: $errorOutput" -ForegroundColor Red
    }
}
catch {
    Write-Host "Exception: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    if (!$process.HasExited) {
        $process.Kill()
    }
    $process.Dispose()
}
