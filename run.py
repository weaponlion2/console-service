from app.main import app
import uvicorn
import multiprocessing

if __name__ == "__main__":
    # REQUIRED for PyInstaller + Uvicorn on Windows
    multiprocessing.freeze_support() 
    
    uvicorn.run(app, host="0.0.0.0", port=11102)