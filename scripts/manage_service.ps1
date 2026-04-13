# --- Configuration Variables ---
$ServiceName  = "MyConsoleService"
$DisplayName  = "My Protected FastAPI Service"
$BaseDir      = $PSScriptRoot 

# Build relative paths automatically
$ExePath      = Join-Path $BaseDir "Application\ConsoleService.exe"
$AppDirectory = Join-Path $BaseDir "Application"
$LogDir       = Join-Path $BaseDir "logs"
$OutLog       = Join-Path $LogDir "out.log"
$ErrLog       = Join-Path $LogDir "err.log"

# Explicit paths to bypass environment variable delays
$global:ChocoPath = "$env:ProgramData\chocolatey\bin\choco.exe"
$global:NssmPath  = "$env:ProgramData\chocolatey\bin\nssm.exe"
$ErrorActionPreference = "Stop"

function Show-Menu {
    # Dynamically check service status for the header
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    $statusText = if ($service) { $service.Status } else { "Not Installed" }
    $statusColor = switch($statusText) { "Running" {"Green"} "Stopped" {"Yellow"} Default {"Red"} }

    Clear-Host
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "   WINDOWS SERVICE & ENVIRONMENT MANAGER      " -ForegroundColor Cyan
    Write-Host "   Service Status: " -NoNewline
    Write-Host "$statusText" -ForegroundColor $statusColor
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "1) Setup Environment (Install Choco & NSSM)"
    Write-Host "2) Register / Reinstall Service"
    Write-Host "3) Unregister (Remove) Service"
    Write-Host "4) Start Service"
    Write-Host "5) Stop Service"
    Write-Host "6) Check Detailed Status (NSSM)"
    Write-Host "7) System Cleanup (Uninstall Choco & NSSM)"
    Write-Host "Q) Quit"
    Write-Host "----------------------------------------------"
}

function Setup-Environment {
    Write-Host "[SETUP] Checking prerequisites..." -ForegroundColor Yellow
    if ((Get-ExecutionPolicy) -eq "Restricted") {
        Set-ExecutionPolicy Bypass -Scope Process -Force
    }

    # Install Chocolatey
    if (!(Test-Path $global:ChocoPath)) {
        Write-Host "[CHOCO] Not found. Installing..." -ForegroundColor Yellow
        [System.Net.ServicePointManager]::SecurityProtocol = 3072
        Invoke-WebRequest https://community.chocolatey.org/install.ps1 -UseBasicParsing | Invoke-Expression
        
        $retry = 0
        while (!(Test-Path $global:ChocoPath) -and $retry -lt 10) {
            Start-Sleep -Seconds 2
            $retry++
        }
    }

    # Install NSSM
    if (!(Test-Path $global:NssmPath)) {
        Write-Host "[NSSM] Installing NSSM via Chocolatey..." -ForegroundColor Yellow
        & "$global:ChocoPath" install nssm -y
        
        $retry = 0
        while (!(Test-Path $global:NssmPath) -and $retry -lt 10) {
            Start-Sleep -Seconds 2
            $retry++
        }
    }
    
    Write-Host "[SUCCESS] Environment is ready." -ForegroundColor Green
    Pause
}

function Register-Service {
    $serviceCheck = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($serviceCheck) {
        Write-Host "[SKIP] Service '$ServiceName' exists. Reconfiguring..." -ForegroundColor Yellow
        & "$global:NssmPath" stop $ServiceName
        & "$global:NssmPath" remove $ServiceName confirm
    }

    Write-Host "[INSTALL] Creating service: $ServiceName" -ForegroundColor Cyan
    & "$global:NssmPath" install $ServiceName "$ExePath"
    & "$global:NssmPath" set $ServiceName AppDirectory "$AppDirectory"
    & "$global:NssmPath" set $ServiceName DisplayName "$DisplayName"
    & "$global:NssmPath" set $ServiceName Start SERVICE_AUTO_START

    if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir }
    & "$global:NssmPath" set $ServiceName AppStdout "$OutLog"
    & "$global:NssmPath" set $ServiceName AppStderr "$ErrLog"

    & "$global:NssmPath" start $ServiceName
    Write-Host "[SUCCESS] Service registered and started." -ForegroundColor Green
    Pause
}

function Unregister-Service {
    if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
        Write-Host "[REMOVE] Stopping and removing $ServiceName..." -ForegroundColor Yellow
        & "$global:NssmPath" stop $ServiceName
        & "$global:NssmPath" remove $ServiceName confirm
        Write-Host "[SUCCESS] Service removed." -ForegroundColor Green
    } else {
        Write-Host "[SKIP] Service not found." -ForegroundColor Gray
    }
    Pause
}

function Start-MyService {
    Write-Host "[START] Attempting to start $ServiceName..." -ForegroundColor Cyan
    & "$global:NssmPath" start $ServiceName
    Pause
}

function Stop-MyService {
    Write-Host "[STOP] Attempting to stop $ServiceName..." -ForegroundColor Yellow
    & "$global:NssmPath" stop $ServiceName
    Pause
}

function Global-Cleanup {
    Write-Host "=== STARTING GLOBAL CLEANUP ===" -ForegroundColor Red
    if (Test-Path $global:ChocoPath) {
        & "$global:ChocoPath" uninstall nssm -y
        Remove-Item -Recurse -Force "$env:ProgramData\chocolatey" -ErrorAction SilentlyContinue
    }

    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $cleanMachinePath = ($machinePath -split ";") | Where-Object { $_ -notlike "*chocolatey*" }
    [Environment]::SetEnvironmentVariable("Path", ($cleanMachinePath -join ";"), "Machine")
    [Environment]::SetEnvironmentVariable("ChocolateyInstall", $null, "Machine")
    
    Write-Host "[SUCCESS] System cleaned." -ForegroundColor Green
    Pause
}

# --- Main Loop ---
do {
    Show-Menu
    $input = Read-Host "Select an option"
    switch ($input) {
        '1' { Setup-Environment }
        '2' { Register-Service }
        '3' { Unregister-Service }
        '4' { Start-MyService }
        '5' { Stop-MyService }
        '6' { 
            if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
                & "$global:NssmPath" status $ServiceName
            } else {
                Write-Host "Service not installed." -ForegroundColor Red
            }
            Pause
        }
        '7' { Global-Cleanup }
        'q' { exit }
    }
} while ($true)