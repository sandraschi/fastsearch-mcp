# Read FastSearch MCP Service Event Logs
# Provides detailed event log analysis for service debugging

param(
    [Parameter(Mandatory=$false)]
    [int]$MaxEvents = 50,
    [Parameter(Mandatory=$false)]
    [ValidateSet("All", "Error", "Warning", "Information")]
    [string]$Level = "All"
)

$ServiceName = "FastSearchMCP"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "FastSearch MCP Service Event Log Reader" "Cyan"
Write-ColorOutput "=======================================" "Cyan"
Write-ColorOutput ""

try {
    # Get events from Application log
    $filter = @{
        LogName = "Application"
        MaxEvents = $MaxEvents
    }
    
    if ($Level -ne "All") {
        $levelMap = @{
            "Error" = 2
            "Warning" = 3
            "Information" = 4
        }
        $filter["Level"] = $levelMap[$Level]
    }
    
    $events = Get-WinEvent -FilterHashtable $filter -ErrorAction Stop | 
        Where-Object { 
            $_.ProviderName -eq $ServiceName -or 
            $_.Message -like "*$ServiceName*" -or
            $_.Message -like "*FastSearch*"
        } | 
        Sort-Object TimeCreated -Descending
    
    if ($events) {
        Write-ColorOutput "Found $($events.Count) events:" "Green"
        Write-ColorOutput ""
        
        foreach ($event in $events) {
            $levelColor = switch ($event.LevelDisplayName) {
                "Error" { "Red" }
                "Warning" { "Yellow" }
                "Information" { "Green" }
                default { "White" }
            }
            
            Write-ColorOutput "[$($event.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss'))] [$($event.LevelDisplayName)]" $levelColor
            Write-ColorOutput "  $($event.Message)" "White"
            Write-ColorOutput ""
        }
        
        # Summary
        $errorCount = ($events | Where-Object { $_.LevelDisplayName -eq "Error" }).Count
        $warningCount = ($events | Where-Object { $_.LevelDisplayName -eq "Warning" }).Count
        $infoCount = ($events | Where-Object { $_.LevelDisplayName -eq "Information" }).Count
        
        Write-ColorOutput "Summary:" "Cyan"
        Write-ColorOutput "  Errors: $errorCount" $(if ($errorCount -gt 0) { "Red" } else { "Green" })
        Write-ColorOutput "  Warnings: $warningCount" $(if ($warningCount -gt 0) { "Yellow" } else { "Green" })
        Write-ColorOutput "  Information: $infoCount" "Green"
    }
    else {
        Write-ColorOutput "⚠️  No events found for FastSearch MCP Service" "Yellow"
        Write-ColorOutput "   This might mean:" "Cyan"
        Write-ColorOutput "   - Service has not been started yet" "Cyan"
        Write-ColorOutput "   - Service is running without errors" "Cyan"
        Write-ColorOutput "   - Events are in a different log" "Cyan"
    }
}
catch {
    Write-ColorOutput "❌ Error reading event logs: $($_.Exception.Message)" "Red"
    Write-ColorOutput "   Make sure you have permission to read the Application event log" "Yellow"
}

