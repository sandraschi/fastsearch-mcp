# FastSearch MCP Service Fix Script
# This script handles the "marked for deletion" issue

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("force-delete", "clean-registry", "restart-service", "help")]
    [string]$Action = "help"
)

$ServiceName = "FastSearchMCP"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Remove-Service-Force {
    Write-ColorOutput "Force deleting stuck service..." "Yellow"
    
    if (-not (Test-Administrator)) {
        Write-ColorOutput "ERROR: Administrator privileges required!" "Red"
        Write-ColorOutput "Please run PowerShell as Administrator and try again." "Yellow"
        return $false
    }
    
    try {
        # Try to stop the service first
        Write-ColorOutput "Attempting to stop service..." "Cyan"
        sc stop $ServiceName 2>$null
        
        # Wait a moment
        Start-Sleep -Seconds 3
        
        # Force delete the service
        Write-ColorOutput "Force deleting service..." "Cyan"
        $result = sc delete $ServiceName 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Service deleted successfully!" "Green"
            Write-ColorOutput "Wait 30 seconds before reinstalling..." "Yellow"
            return $true
        }
        else {
            Write-ColorOutput "❌ Service deletion failed: $result" "Red"
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ Error during service deletion: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Clear-Service-Registry {
    Write-ColorOutput "Cleaning service registry entries..." "Yellow"
    
    if (-not (Test-Administrator)) {
        Write-ColorOutput "ERROR: Administrator privileges required!" "Red"
        Write-ColorOutput "Please run PowerShell as Administrator and try again." "Yellow"
        return $false
    }
    
    try {
        $regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\$ServiceName"
        
        if (Test-Path $regPath) {
            Write-ColorOutput "Removing registry entry: $regPath" "Cyan"
            Remove-Item -Path $regPath -Recurse -Force
            Write-ColorOutput "✅ Registry entry removed!" "Green"
        }
        else {
            Write-ColorOutput "Registry entry not found (already clean)" "Yellow"
        }
        
        # Also check for any pending deletion entries
        $pendingPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\PendingFileRenameOperations"
        if (Test-Path $pendingPath) {
            Write-ColorOutput "Checking for pending file operations..." "Cyan"
            $pending = Get-ItemProperty -Path $pendingPath -ErrorAction SilentlyContinue
            if ($pending) {
                Write-ColorOutput "Found pending operations - may need system restart" "Yellow"
            }
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "❌ Error cleaning registry: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Restart-Service-Manager {
    Write-ColorOutput "Restarting Service Control Manager..." "Yellow"
    
    if (-not (Test-Administrator)) {
        Write-ColorOutput "ERROR: Administrator privileges required!" "Red"
        Write-ColorOutput "Please run PowerShell as Administrator and try again." "Yellow"
        return $false
    }
    
    try {
        Write-ColorOutput "Stopping Service Control Manager..." "Cyan"
        Stop-Service -Name "Service Control Manager" -Force -ErrorAction SilentlyContinue
        
        Start-Sleep -Seconds 5
        
        Write-ColorOutput "Starting Service Control Manager..." "Cyan"
        Start-Service -Name "Service Control Manager" -ErrorAction SilentlyContinue
        
        Write-ColorOutput "✅ Service Control Manager restarted!" "Green"
        return $true
    }
    catch {
        Write-ColorOutput "❌ Error restarting Service Control Manager: $($_.Exception.Message)" "Red"
        Write-ColorOutput "You may need to restart Windows to clear the service state." "Yellow"
        return $false
    }
}

function Show-Help {
    Write-ColorOutput "FastSearch MCP Service Fix Tool" "Cyan"
    Write-ColorOutput "===============================" "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "This tool fixes the 'marked for deletion' service issue." "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "Actions:" "Cyan"
    Write-ColorOutput "  force-delete    - Force delete the stuck service" "Cyan"
    Write-ColorOutput "  clean-registry  - Clean service registry entries" "Cyan"
    Write-ColorOutput "  restart-service - Restart Service Control Manager" "Cyan"
    Write-ColorOutput "  help           - Show this help" "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "Recommended sequence:" "Cyan"
    Write-ColorOutput "1. .\fix-service.ps1 force-delete" "Cyan"
    Write-ColorOutput "2. Wait 30 seconds" "Cyan"
    Write-ColorOutput "3. .\install-service.ps1 install" "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "If that doesn't work:" "Cyan"
    Write-ColorOutput "1. .\fix-service.ps1 clean-registry" "Cyan"
    Write-ColorOutput "2. Restart Windows" "Cyan"
    Write-ColorOutput "3. .\install-service.ps1 install" "Cyan"
}

# Main execution
switch ($Action.ToLower()) {
    "force-delete" {
        Remove-Service-Force
    }
    "clean-registry" {
        Clear-Service-Registry
    }
    "restart-service" {
        Restart-Service-Manager
    }
    "help" {
        Show-Help
    }
    default {
        Write-ColorOutput "Unknown action: $Action" "Red"
        Show-Help
    }
}
