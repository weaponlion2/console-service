import sys
import os, platform

class FeigReaderProvider:
    """
    A high-level provider to interact with FEIG RFID Readers.
    Designed for 'plug and call' usage.
    """
    
    def __init__(self, package_path="app/sdk/feig"):
        """
        Initialize the provider and setup DLL dependencies.
        :param package_path: Path to the directory containing the 'feig_reader' package.
        """
        self._setup_dlls(package_path)
        
        packageName = "feig_reader_window" if platform.system().lower() == "Windows".lower() else "feig_reader_linux"
        print(f"Using package: {packageName}")
        # Add package to sys.path
        abs_package_path = os.path.abspath(f"{package_path}/" + packageName)
        if abs_package_path not in sys.path:
            sys.path.append(abs_package_path)
            
        try:
            # print(f"Attempting to import 'feig_reader' from {abs_package_path}")
            # print(f"Current sys.path: {sys.path}")
            import feig_reader  # Ensure this matches the actual package structure
            # print(f"Import : {feig_reader}")  
            self.reader = feig_reader.Reader()
            self.is_connected = False
        except ImportError as e:
            raise ImportError(f"Could not find 'feig_reader' package in {abs_package_path}. "
                              "Ensure the project is built and the path is correct.") from e

    
    def _setup_dlls(self, package_path):
        """Setup Windows DLL search paths for the FEIG SDK."""
        if platform.system().lower() == "Windows".lower():
            dll_dir = os.path.abspath(os.path.join(package_path, "feig_reader_window"))
            if os.path.exists(dll_dir):
                # Add to PATH for older DLL loading
                os.environ['PATH'] = dll_dir + os.pathsep + os.environ['PATH']
                # Add to DLL directory for Python 3.8+
                if hasattr(os, 'add_dll_directory'):
                    os.add_dll_directory(dll_dir)
            else:
                print(f"Warning: DLL directory not found at {dll_dir}")
        else:
            # For Linux, ensure the shared library path is set
            lib_dir = os.path.abspath(os.path.join(package_path, "feig_reader_linux"))
            if os.path.exists(lib_dir):
                os.environ['LD_LIBRARY_PATH'] = lib_dir + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')
            else:
                print(f"Warning: Shared library directory not found at {lib_dir}")


    def connect(self):
        """Connect to the first available USB reader."""
        try:
            self.reader.connect_usb()
            self.is_connected = True
            return True
        except Exception:
            return False

    def disconnect(self):
        """Disconnect the reader."""
        if self.is_connected:
            try:
                self.reader.disconnect()
            finally:
                self.is_connected = False

    def inventory(self, timeout_ms=1000):
        """
        Perform an inventory scan.
        :return: List of TagInfo objects or empty list on failure.
        """
        if not self.is_connected:
            return []
            
        try:
            return self.reader.inventory(timeout_ms=timeout_ms)
        except Exception:
            return []

    def read_tag(self, tag_idx=0, offset=0, noOfBlocks=4):
        """
        Read data from a tag.
        :return: Hex string of data or None if failed.
        """
        if not self.is_connected:
            return None
            
        try:
            return self.reader.read(idx=tag_idx, offset=offset, noOfBlocks=noOfBlocks)
        except Exception:
            return None

    def write_tag(self, tag_idx=0, offset=0, data=None):
        """
        Write data to a tag.
        :return: True if successful, False otherwise.
        """
        if not self.is_connected:
            return False
            
        try:
            self.reader.write(idx=tag_idx, offset=offset, data=data)
            return True
        except Exception:
            return False
    
            
    def write_eas(self, tag_idx=0, value=True):
        """
        Write eas status to a tag.
        :return: True if successful, False otherwise.
        """
        if not self.is_connected:
            return False
            
        try:
            self.reader.write_eas(idx=tag_idx, enabled=value)
            return True
        except Exception:   
            return False

    def read_eas(self, tag_idx=0):
        """
        Read eas status from a tag.
        :return: Boolean string of data or None if failed.
        """
        if not self.is_connected:
            return None
            
        try:
            value = self.reader.read_eas(idx=tag_idx) 
            return True if value == "true" else False
        except Exception as ex:
            print(ex)
            return None

    def write_afi(self, tag_idx=0, afiValue="0"):
        """
        Write afi value to a tag.
        :return: True if successful, False otherwise.
        """
        if not self.is_connected:
            return False
            
        try:
            self.reader.write_afi(idx=tag_idx, afiValue=afiValue.__str__())
            return True
        except Exception as ex:
            print(ex)
            return False

    def read_afi(self, tag_idx=0):
        """
        Read afi value from a tag.
        :return: string of data or None if failed.
        """
        if not self.is_connected:
            return None
            
        try:
            value = self.reader.read_afi(idx=tag_idx) 
            return value
        except Exception as ex:
            print(ex)
            return None