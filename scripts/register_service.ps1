# --- Configuration Variables ---
$ServiceName = "MyConsoleService"
$ExePath     = "D:\TPAD\ServiceCode\dist\FastAPIService.exe"
$AppDirectory = "D:\TPAD\ServiceCode\dist\"
$LogDir      = "D:\TPAD\ServiceCode\dist"
$OutLog      = "$LogDir\out.log"
$ErrLog      = "$LogDir\err.log"

# --- 1. Check if Service Already Exists ---
$serviceCheck = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($serviceCheck) {
    Write-Host "[SKIP] Service '$ServiceName' already exists. Stopping and removing to reconfigure..." -ForegroundColor Yellow
    nssm stop $ServiceName
    nssm remove $ServiceName confirm
}

# --- 2. Create the Service ---
Write-Host "[INSTALL] Creating service: $ServiceName" -ForegroundColor Cyan
nssm install $ServiceName "$ExePath"

# --- 3. Configure via Command Line (The "GUI" Steps) ---

# Application Tab Settings
nssm set $ServiceName AppDirectory "$AppDirectory"

# Details Tab Settings
nssm set $ServiceName DisplayName "My Protected FastAPI Service"
nssm set $ServiceName Start SERVICE_AUTO_START

# I/O Tab (Logging)
# Ensure the log directory exists first
if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir }

nssm set $ServiceName AppStdout "$OutLog"
nssm set $ServiceName AppStderr "$ErrLog"

# --- 4. Start the Service ---
Write-Host "[START] Starting $ServiceName..." -ForegroundColor Green
nssm start $ServiceName

# --- 5. Verify ---
$status = nssm status $ServiceName
Write-Host "[STATUS] Current status: $status" -ForegroundColor White