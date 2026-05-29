Step 1: Get NSSM
Download NSSM from the official site (nssm.cc) or install it via an Administrator PowerShell using Scoop/Chocolatey if you prefer:

    # choco install nssm

Step 2: Install via the NSSM GUI
NSSM has a fantastic GUI that makes configuring paths and logs trivial. In your Administrator prompt, run:

    # nssm install MyFastAPIService

A GUI window will pop up. Configure these specific tabs:

1. Application Tab (Crucial):

Path: Browse to your compiled FastAPI app: D:\TPAD\ServiceCode\dist\FastAPIService.exe

Directory: This should auto-fill to D:\TPAD\ServiceCode\dist\. This acts as your cwd (Current Working Directory).

Arguments: Leave blank (unless your .exe requires them).

2. Details Tab:

Display name: Enter what you want to see in the Windows Services list (e.g., My Protected FastAPI Service).

Startup type: Automatic (or Automatic Delayed Start).

3. I/O Tab (Highly Recommended for Logging):
Since you are bypassing your python wrapper, you need NSSM to capture Uvicorn's console output.

Output (stdout): D:\TPAD\ServiceCode\out.log

Error (stderr): D:\TPAD\ServiceCode\err.log

Click "Install service".

Step 3: Start the Service
You can now start it from the standard Windows services.msc menu, or directly from your command line:

    # nssm start MyFastAPIService


Set-ExecutionPolicy Bypass -Scope Process

Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

choco -v

pyinstaller --onefile 
    --name FastAPIService 
    --hidden-import=uvicorn 
    --hidden-import=fastapi 
    --hidden-import=pydantic 
    --hidden-import=app.api 
    --hidden-import=app.services 
    --hidden-import=app.schemas 
    --hidden-import=app.integrations 
    --hidden-import=win32timezone 
    run.py



powershell -ExecutionPolicy Bypass -File .\setup.ps1


pyinstaller --onefile 
    --name ConsoleService 
    --hidden-import=uvicorn 
    --hidden-import=fastapi 
    --hidden-import=pydantic 
    --hidden-import=app.api 
    --hidden-import=app.services 
    --hidden-import=app.schemas 
    --hidden-import=app.integrations 
    --hidden-import=win32timezone 
    run.py