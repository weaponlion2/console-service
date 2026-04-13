# Fail fast
$ErrorActionPreference = "Stop"

Write-Host "=== STARTING CLEAN UNINSTALL ===" -ForegroundColor Cyan

# --- 1. Define paths ---
$chocoRoot = "$env:ProgramData\chocolatey"
$chocoBin  = "$chocoRoot\bin\choco.exe"

# --- 2. Uninstall NSSM via Chocolatey (if possible) ---
if (Test-Path $chocoBin) {
    Write-Host "[NSSM] Attempting uninstall via Chocolatey..." -ForegroundColor Yellow
    try {
        & "$chocoBin" uninstall nssm -y
    } catch {
        Write-Host "[WARN] NSSM uninstall via choco failed (may not be installed)." -ForegroundColor DarkYellow
    }
}

# --- 3. Remove NSSM manually if still present ---
$nssmCmd = Get-Command nssm -ErrorAction SilentlyContinue
if ($nssmCmd) {
    Write-Host "[NSSM] Removing leftover NSSM binary..." -ForegroundColor Yellow
    try {
        Remove-Item -Force $nssmCmd.Source
    } catch {
        Write-Host "[WARN] Could not delete NSSM binary." -ForegroundColor DarkYellow
    }
} else {
    Write-Host "[NSSM] Not found in PATH." -ForegroundColor Gray
}

# --- 4. Uninstall Chocolatey completely ---
if (Test-Path $chocoRoot) {
    Write-Host "[CHOCO] Removing Chocolatey folder..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $chocoRoot
} else {
    Write-Host "[CHOCO] Chocolatey folder not found." -ForegroundColor Gray
}

# --- 5. Clean PATH Environment Variable ---
Write-Host "[CLEANUP] Removing Chocolatey from PATH..." -ForegroundColor Yellow

$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath    = [Environment]::GetEnvironmentVariable("Path", "User")

$cleanMachinePath = ($machinePath -split ";") | Where-Object { $_ -notlike "*chocolatey*" }
$cleanUserPath    = ($userPath -split ";") | Where-Object { $_ -notlike "*chocolatey*" }

[Environment]::SetEnvironmentVariable("Path", ($cleanMachinePath -join ";"), "Machine")
[Environment]::SetEnvironmentVariable("Path", ($cleanUserPath -join ";"), "User")

# --- 6. Remove Chocolatey environment variables ---
Write-Host "[CLEANUP] Removing Chocolatey environment variables..." -ForegroundColor Yellow

[Environment]::SetEnvironmentVariable("ChocolateyInstall", $null, "Machine")
[Environment]::SetEnvironmentVariable("ChocolateyLastPathUpdate", $null, "Machine")

# --- 7. Final Check ---
Write-Host "`n=== FINAL STATUS ===" -ForegroundColor Cyan

$chocoCheck = Get-Command choco -ErrorAction SilentlyContinue
$nssmCheck  = Get-Command nssm -ErrorAction SilentlyContinue

if (!$chocoCheck) {
    Write-Host "Chocolatey: REMOVED" -ForegroundColor Green
} else {
    Write-Host "Chocolatey: STILL PRESENT" -ForegroundColor Red
}

if (!$nssmCheck) {
    Write-Host "NSSM: REMOVED" -ForegroundColor Green
} else {
    Write-Host "NSSM: STILL PRESENT" -ForegroundColor Red
}

Write-Host "`n=== CLEANUP COMPLETE ===" -ForegroundColor Cyan