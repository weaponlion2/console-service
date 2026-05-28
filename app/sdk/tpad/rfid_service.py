from pathlib import Path
import os
import sys
import time
import threading

class RFIDService:
    def __init__(self, driver_path="libs"):
        """
        Initialize the RFID Service.
        :param driver_path: Path to the directory containing rfid_native.pyd and DLLs.
                           Defaults to the current directory of this file.
        """
        if driver_path is None:
            self.driver_path = Path(__file__).resolve().parent
        else:
            self.driver_path = (
                Path(__file__).resolve().parent / driver_path
            )

        self.driver_path = str(self.driver_path)
        self._lock = threading.Lock()
        
        self._setup_environment()
        
        # Import the native module
        try:
            import rfid_native
            self.api = rfid_native.RFIDReader()
            
        except ImportError as e:
            print(f"Error: Could not load rfid_native module. {e}")
            raise

        self._initialize_drivers()

    def _setup_environment(self):
        """Add the driver path to sys.path and DLL search path."""
        if self.driver_path not in sys.path:
            sys.path.append(self.driver_path)
        
        if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(self.driver_path)
            except Exception as e:
                print(f"Warning: Could not add DLL directory: {e}")

    def _initialize_drivers(self):
        """Load reader drivers from the device_driver subdirectory."""

        driver_path = (
            Path(self.driver_path).resolve() / "device_driver"
        )

        # Add trailing slash only if SDK requires it
        path_str = str(driver_path) + os.path.sep
        
        with self._lock:
            if self.api.load_drivers(path_str):
                count = self.api.get_driver_count()

                if count > 0:
                    print(f"RFID Drivers initialized. Loaded {count} drivers.")
                    return

        print("Warning: Failed to load RFID drivers.")

    def connect(self, connection_str="RDType=M201;CommType=USB;AddrMode=0"):
        """Connect to the RFID reader."""
        with self._lock:
            print(f"Connecting to reader: {connection_str}...")
            if self.api.initialize(connection_str):
                print("Connected successfully.")
                return True
            print("Connection failed.")
            return False

    def disconnect(self):
        """Disconnect from the reader."""
        with self._lock:
            self.api.shutdown()
            print("Disconnected.")

    def get_inventory(self):
        """Perform an inventory scan and return a list of tags."""
        with self._lock:
            if not self.api.start_multi_inventory():
                print("Inventory scan failed.")
                return []
            
            tags = self.api.get_detected_tags()
            return tags

    def read_tag_blocks(self, uid, start_block, count):
        """
        Read multiple blocks from an ISO 15693 tag.
        :param uid: Tag UID (hex string)
        :param start_block: Starting block number
        :param count: Number of blocks to read
        """
        with self._lock:
            # Connect to the specific tag first
            if not self.api.connect_tag(uid, 1): # 1 = ISO 15693
                print(f"Failed to connect to tag {uid}")
                return None
            
            results = []
            try:
                for i in range(start_block, start_block + count):
                    data = self.api.iso15693_read_block(i)
                    if data:
                        results.append(data)
                    else:
                        print(f"Failed to read block {i}")
                        results.append(None)
            finally:
                self.api.disconnect_tag()
                
            return results

    def write_tag_block(self, uid, block_num, data):
        """
        Write a single block to an ISO 15693 tag.
        :param uid: Tag UID
        :param block_num: Block number
        :param data: List of 4 bytes (uint8)
        """
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                print(f"Failed to connect to tag {uid}")
                return False
                
            try:
                success = self.api.iso15693_write_block(block_num, data)
                return success
            finally:
                self.api.disconnect_tag()

    def get_tag_system_info(self, uid):
        """
        Get ISO 15693 system information (DSFID, AFI, etc.)
        """
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return None
            try:
                info = self.api.iso15693_get_system_info()
                return {
                    "dsfid": info[0],
                    "afi": info[1],
                    "vic": info[2],
                    "blk_count": info[3],
                    "blk_size": info[4]
                }
            finally:
                self.api.disconnect_tag()

    def write_afi(self, uid, afi):
        """Write AFI value to ISO 15693 tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.iso15693_write_afi(afi)
            finally:
                self.api.disconnect_tag()

    def lock_afi(self, uid):
        """Lock AFI value on ISO 15693 tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.iso15693_lock_afi()
            finally:
                self.api.disconnect_tag()

    def enable_eas(self, uid):
        """Enable EAS (Electronic Article Surveillance) on NXP iCode SLI tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.nxp_icodesli_enable_eas()
            finally:
                self.api.disconnect_tag()

    def disable_eas(self, uid):
        """Disable EAS on NXP iCode SLI tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.nxp_icodesli_disable_eas()
            finally:
                self.api.disconnect_tag()

    def check_eas(self, uid):
        """Check if EAS alarm is active on NXP iCode SLI tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return None
            try:
                return self.api.nxp_icodesli_check_eas()
            except RuntimeError:
                return None
            finally:
                self.api.disconnect_tag()

    def write_eas_id(self, uid, eas_id):
        """Write EAS ID to NXP iCode SLI tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.nxp_icodesli_write_eas_id(eas_id)
            finally:
                self.api.disconnect_tag()

    def lock_eas(self, uid):
        """Lock EAS on NXP iCode SLI tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.nxp_icodesli_lock_eas()
            finally:
                self.api.disconnect_tag()

    def eas_alarm(self, uid):
        """Trigger EAS Alarm on NXP iCode SLI tag and return EAS data."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return None
            try:
                return self.api.nxp_icodesli_eas_alarm()
            except RuntimeError:
                return None
            finally:
                self.api.disconnect_tag()

    def enable_em4237_eas(self, uid):
        """Enable EAS on EM4237 tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.em4237sli_enable_eas()
            finally:
                self.api.disconnect_tag()

    def disable_em4237_eas(self, uid):
        """Disable EAS on EM4237 tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.em4237sli_disable_eas()
            finally:
                self.api.disconnect_tag()

    def check_em4237_eas(self, uid):
        """Check if EAS alarm is active on EM4237 tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return None
            try:
                return self.api.em4237sli_check_eas()
            except RuntimeError:
                return None
            finally:
                self.api.disconnect_tag()

    def lock_em4237_eas(self, uid):
        """Lock EAS on EM4237 tag."""
        with self._lock:
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.em4237sli_lock_eas()
            finally:
                self.api.disconnect_tag()

    def get_lib_version(self):
        with self._lock:
            return self.api.get_lib_version()
