# (fail fast)
$ErrorActionPreference = "Stop"

# --- 1. Execution Policy ---
$currentPolicy = Get-ExecutionPolicy
if ($currentPolicy -eq "Restricted") {
    Write-Host "[POLICY] Bypassing execution policy for this session..." -ForegroundColor Cyan
    Set-ExecutionPolicy Bypass -Scope Process -Force
}

# --- 2. Define Chocolatey Path ---
$chocoPath = "$env:ProgramData\chocolatey\bin\choco.exe"

# --- 3. Ensure Chocolatey Installed ---
if (!(Test-Path $chocoPath)) {
    Write-Host "[CHOCO] Not found or broken. Cleaning and installing..." -ForegroundColor Yellow

    # Cleanup any broken install
    Remove-Item -Recurse -Force "$env:ProgramData\chocolatey" -ErrorAction SilentlyContinue

    # Install Chocolatey
    [System.Net.ServicePointManager]::SecurityProtocol = 3072
    iwr https://community.chocolatey.org/install.ps1 -UseBasicParsing | iex

    # Wait until choco.exe exists
    $maxRetries = 10
    $retry = 0
    while (!(Test-Path $chocoPath) -and $retry -lt $maxRetries) {
        Start-Sleep -Seconds 2
        $retry++
    }

    if (!(Test-Path $chocoPath)) {
        Write-Error "[CHOCO] Installation failed. choco.exe not found."
        exit 1
    }

    Write-Host "[CHOCO] Installed successfully." -ForegroundColor Green
} else {
    Write-Host "[CHOCO] Already installed." -ForegroundColor Gray
}

# --- 4. Refresh PATH ---
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path","User")

# --- 5. Verify Chocolatey ---
Write-Host "[VERIFY] Chocolatey version:" -ForegroundColor Cyan
& "$chocoPath" -v

# --- 6. Install NSSM if missing ---
$nssmCmd = Get-Command nssm -ErrorAction SilentlyContinue

if (!$nssmCmd) {
    Write-Host "[NSSM] Not found. Installing..." -ForegroundColor Yellow
    & "$chocoPath" install nssm -y

    # Refresh PATH again
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "[NSSM] Already installed." -ForegroundColor Gray
}

# --- 7. Final Verification ---
Write-Host "`n--- FINAL STATUS ---" -ForegroundColor Cyan

Write-Host "Choco Version: $(& "$chocoPath" -v)"

$nssmCmd = Get-Command nssm -ErrorAction SilentlyContinue
if ($nssmCmd) {
    Write-Host "NSSM Path: $($nssmCmd.Source)"
    nssm version
} else {
    Write-Host "NSSM NOT FOUND" -ForegroundColor Red
}