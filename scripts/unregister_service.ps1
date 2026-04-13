# --- Configuration ---
$ServiceName = "MyConsoleService"

Write-Host "--- Starting Uninstallation Process ---" -ForegroundColor Cyan

# 1. Stop and Remove the Service
$serviceCheck = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($serviceCheck) {
    Write-Host "[SERVICE] Found $ServiceName. Stopping and removing..." -ForegroundColor Yellow
    # NSSM stop handles the service termination
    nssm stop $ServiceName
    # 'confirm' bypasses the "Are you sure?" GUI popup
    nssm remove $ServiceName confirm
    Write-Host "[SERVICE] Service removed successfully." -ForegroundColor Green
} else {
    Write-Host "[SKIP] Service '$ServiceName' not found." -ForegroundColor Gray
}


Write-Host "--- Cleanup Complete ---" -ForegroundColor Cyan