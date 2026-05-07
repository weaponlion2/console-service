import os
import sys
import logging

def get_log_path():
    """
    Detects the log directory path.
    Specifically handles the scenario where the application is built as an executable.
    The logs should be stored in a directory sibling to the 'Application' folder (./../logs/).
    """
    if getattr(sys, 'frozen', False):
        # Path where the .exe is located
        base_dir = os.path.dirname(sys.executable)
    else:
        # Path where the script is located (app/workers)
        # We go up two levels to reach the root if this is in app/workers/logger.py
        # However, the user's specific request is for the build scenario.
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct path to ../logs/ relative to the base directory
    # If base_dir is 'Application/', then ../logs is what was requested.
    log_dir = os.path.abspath(os.path.join(base_dir, "..", "logs"))
    
    # Ensure the logs directory exists
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    return os.path.join(log_dir, "logging.txt")

# Initialize log file path
log_file_path = get_log_path()

# Custom FileHandler that flushes after every write to prevent "stuck" logs
class ImmediateFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

# Create a dedicated logger instance
logger = logging.getLogger("WorkerLogger")
logger.setLevel(logging.INFO)

# Prevent duplicate handlers if the module is reloaded
if not logger.handlers:
    # File Handler with immediate flush
    file_handler = ImmediateFileHandler(log_file_path, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

# Disable propagation to the root logger to avoid double-logging or interference from other frameworks
logger.propagate = False

logger.info(f"Logger initialized. Writing to: {log_file_path}")

