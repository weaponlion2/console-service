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

        self.is_connected = False
        self._initialize_drivers()

    def _check_connection(self):
        """Verify reader physical connection. Disconnects and raises error on failure."""
        if not self.is_connected:
            raise RuntimeError("RFID Reader is not connected.")
        try:
            info = self.api.get_reader_info()
            if "Reader not connected" in info or not info:
                self.disconnect()
                raise RuntimeError("RFID Reader has been physically disconnected.")
        except Exception as e:
            self.disconnect()
            raise RuntimeError(f"RFID Reader connection lost: {e}")

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

    def connect(self, connection_str="RDType=RL8000;CommType=USB;AddrMode=0"):
        """Connect to the RFID reader."""
        with self._lock:
            print(f"Connecting to reader: {connection_str}...")
            if self.api.initialize(connection_str):
                self.is_connected = True
                print("Connected successfully.")
                return True
            self.is_connected = False
            print("Connection failed.")
            return False

    def disconnect(self):
        """Disconnect from the reader."""
        with self._lock:
            self.api.shutdown()
            self.is_connected = False
            print("Disconnected.")

    def get_inventory(self):
        """Perform an inventory scan and return a list of tags."""
        with self._lock:
            self._check_connection()
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
            self._check_connection()
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
            self._check_connection()
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
            self._check_connection()
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
            self._check_connection()
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.iso15693_write_afi(afi)
            finally:
                self.api.disconnect_tag()

    def lock_afi(self, uid):
        """Lock AFI value on ISO 15693 tag."""
        with self._lock:
            self._check_connection()
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.iso15693_lock_afi()
            finally:
                self.api.disconnect_tag()

    def enable_eas(self, uid):
        """Enable EAS (Electronic Article Surveillance) on NXP iCode SLI tag."""
        with self._lock:
            self._check_connection()
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.nxp_icodesli_enable_eas()
            finally:
                self.api.disconnect_tag()

    def disable_eas(self, uid):
        """Disable EAS on NXP iCode SLI tag."""
        with self._lock:
            self._check_connection()
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.nxp_icodesli_disable_eas()
            finally:
                self.api.disconnect_tag()

    def check_eas(self, uid):
        """Check if EAS alarm is active on NXP iCode SLI tag."""
        with self._lock:
            self._check_connection()
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
            self._check_connection()
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.nxp_icodesli_write_eas_id(eas_id)
            finally:
                self.api.disconnect_tag()

    def lock_eas(self, uid):
        """Lock EAS on NXP iCode SLI tag."""
        with self._lock:
            self._check_connection()
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.nxp_icodesli_lock_eas()
            finally:
                self.api.disconnect_tag()

    def eas_alarm(self, uid):
        """Trigger EAS Alarm on NXP iCode SLI tag and return EAS data."""
        with self._lock:
            self._check_connection()
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
            self._check_connection()
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.em4237sli_enable_eas()
            finally:
                self.api.disconnect_tag()

    def disable_em4237_eas(self, uid):
        """Disable EAS on EM4237 tag."""
        with self._lock:
            self._check_connection()
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.em4237sli_disable_eas()
            finally:
                self.api.disconnect_tag()

    def check_em4237_eas(self, uid):
        """Check if EAS alarm is active on EM4237 tag."""
        with self._lock:
            self._check_connection()
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
            self._check_connection()
            if not self.api.connect_tag(uid, 1):
                return False
            try:
                return self.api.em4237sli_lock_eas()
            finally:
                self.api.disconnect_tag()

    def get_lib_version(self):
        with self._lock:
            return self.api.get_lib_version()

    # --- Private Helpers for MIFARE S50 Card Handling ---
    def _is_trailer_block(self, block):
        if block < 0 or block > 255:
            raise ValueError("Invalid block number")
        if block < 128:
            return block % 4 == 3
        return (block - 128) % 16 == 15

    def _get_sector_trailer_block(self, block):
        if block < 0 or block > 255:
            raise ValueError("Invalid block number")
        if block < 128:
            sector = block // 4
            return sector * 4 + 3
        else:
            sector = (block - 128) // 16 + 32
            return 128 + (sector - 32) * 16 + 15

    def _get_trailer_block_from_sector(self, sector):
        if sector < 0 or sector > 39:
            raise ValueError("Invalid sector number (0-39)")
        if sector < 32:
            return sector * 4 + 3
        else:
            return 128 + (sector - 32) * 16 + 15

    def _get_available_blocks(self, start_block, data_length):
        import math
        blocks_needed = math.ceil(data_length / 16)
        result = []
        block = start_block
        while len(result) < blocks_needed and block <= 255:
            if not self._is_trailer_block(block):
                result.append(block)
            block += 1
        if len(result) < blocks_needed:
            raise ValueError("Not enough space available on card")
        return result

    def _normalize_key(self, key):
        if isinstance(key, str):
            key = key.replace(" ", "").replace(":", "")
            if len(key) != 12:
                raise ValueError("Key must be 12 hex characters")
            return list(bytes.fromhex(key))
        if isinstance(key, (list, tuple, bytes)):
            if len(key) != 6:
                raise ValueError("Key must be 6 bytes")
            return list(key)
        raise ValueError("Key must be 6-byte list/bytes or 12-character hex string")

    # --- Public MIFARE Card Service Methods ---
    def get_card_info(self, uid):
        """Get card information for the specified UID."""
        with self._lock:
            tags = self.api.get_detected_tags()
            for tag in tags:
                if tag.uid == uid:
                    return {
                        "uid": tag.uid,
                        "air_protocol": tag.air_protocol,
                        "protocol_name": tag.protocol_name,
                        "tag_type": tag.tag_type,
                        "tag_type_name": tag.tag_type_name,
                        "antenna_id": tag.antenna_id
                    }
            return None
    
    @staticmethod 
    def byte_array_to_hex(byte_array):
        return ''.join(f'{b:02X}' for b in byte_array)

    def read_card(self, uid, block, length, key="FFFFFFFFFFFF"):
        """
        Read custom byte length starting at block, automatically skipping sector trailers.
        Sector trailers are never read - they contain security keys and access bits.
        :param uid: Card UID
        :param block: Starting block index (0-255)
        :param length: Total byte count to read (1-3840)
        :param key: Hex string or 6-byte list authentication key
        """
        tags = self.get_inventory()
        if not tags:
            return {"status": False, "data": None, "message": "No tags found in inventory", "readerstatus": "NO_TAGS"}

        with self._lock:
            self._check_connection()
            
            # Validate input parameters
            if not isinstance(length, int) or length < 1 or length > 3840:
                return {"status": False, "data": None, "message": "Length must be 1-3840 bytes", "readerstatus": "BAD_REQUEST"}
            if not isinstance(block, int) or block < 0 or block > 255:
                return {"status": False, "data": None, "message": "Block must be 0-255", "readerstatus": "BAD_REQUEST"}
            
            # Prevent reading from sector trailer blocks
            if self._is_trailer_block(block):
                return {"status": False, "data": None, "message": f"Cannot read from trailer block {block}", "readerstatus": "BAD_REQUEST"}
            
            try:
                norm_key = self._normalize_key(key)
                blocks = self._get_available_blocks(block, length)  # Auto-skips trailers
            except Exception as e:
                return {"status": False, "data": None, "message": str(e), "readerstatus": "BAD_REQUEST"}

            if not self.api.connect_tag(uid, 2): # 2 = ISO 14443A
                return {"status": False, "data": None, "message": "Failed to connect to tag", "readerstatus": "CONNECT_FAILED"}

            block_data = bytearray()
            current_sector = None
            try:
                for block in blocks:
                    # Authenticate once per sector (optimize unnecessary auths)
                    block_sector = block // 4 if block < 128 else (block - 128) // 16 + 32
                    if current_sector != block_sector:
                        trailer = self._get_sector_trailer_block(block)
                        if not self.api.iso14443a_authenticate(trailer, 0, norm_key):
                            return {"status": False, "data": None, "message": f"Authentication failed for sector {block_sector}", "readerstatus": "AUTH_FAILED"}
                        current_sector = block_sector
                    
                    data = self.api.iso14443a_read_block(block)
                    if not data:
                        return {"status": False, "data": None, "message": f"Failed to read block {block}", "readerstatus": "READ_FAILED"}
                    block_data.extend(data)
            finally:
                self.api.disconnect_tag()

            hex_data = RFIDService.byte_array_to_hex(block_data)[: length * 2]
            return {
                "status": True,
                "data": (hex_data),
                "message": f"Successfully read {length} bytes",
                "readerstatus": "CARD_VALID"
            }   

    def write_card(self, uid, block, data, key="FFFFFFFFFFFF"):
        """
        Write data bytes or hex string to card starting at block, skipping sector trailers.
        Sector trailer blocks are NEVER written - they contain security keys and access bits.
        :param uid: Card UID
        :param block: Starting block index (0-255, not a trailer)
        :param data: Quoted ASCII string, hex string, or list of integers
        :param key: Hex string or 6-byte list authentication key
        """
        # Validate block - MUST NOT be a trailer
        if not isinstance(block, int) or block < 0 or block > 255:
            return {"status": False, "message": "Block must be 0-255", "readerstatus": "BAD_REQUEST"}
        if self._is_trailer_block(block):
            return {"status": False, "message": f"Cannot write to trailer block {block}. Start from a normal data block.", "readerstatus": "BAD_REQUEST"}
        
        if isinstance(data, str):
            if (data.startswith('"') and data.endswith('"')) or (data.startswith("'") and data.endswith("'")):
                raw_bytes = data[1:-1].encode('ascii')
            else:
                try:
                    clean_data = data.replace(" ", "").replace(":", "")
                    raw_bytes = bytes.fromhex(clean_data)
                except ValueError:
                    return {"status": False, "message": "Invalid hex format. Wrapped ASCII string in quotes.", "readerstatus": "BAD_REQUEST"}
        elif isinstance(data, (list, tuple, bytes)):
            raw_bytes = bytes(data)
        else:
            return {"status": False, "message": "Data must be string, hex, or list/bytes", "readerstatus": "BAD_REQUEST"}

        if len(raw_bytes) % 16 != 0:
            pad_len = 16 - (len(raw_bytes) % 16)
            raw_bytes = raw_bytes + b'\x00' * pad_len

        with self._lock:
            self._check_connection()
            try:
                norm_key = self._normalize_key(key)
                blocks = self._get_available_blocks(block, len(raw_bytes))  # Automatically skips trailers
            except Exception as e:
                return {"status": False, "message": str(e), "readerstatus": "BAD_REQUEST"}

            # Safety check: Verify no trailer blocks in write list (should never happen with _get_available_blocks)
            for block in blocks:
                if self._is_trailer_block(block):
                    return {"status": False, "message": f"SAFETY: Attempted to write to trailer block {block}. This should not happen.", "readerstatus": "INTERNAL_ERROR"}

            if not self.api.connect_tag(uid, 2):
                return {"status": False, "message": "Failed to connect to tag", "readerstatus": "CONNECT_FAILED"}

            try:
                for i in range(0, len(raw_bytes), 16):
                    block = blocks[i // 16]
                    chunk = list(raw_bytes[i:i+16])
                    
                    trailer = self._get_sector_trailer_block(block)
                    self.api.iso14443a_authenticate(trailer, 0, norm_key)
                    
                    if not self.api.iso14443a_write_block(block, chunk):
                        return {"status": False, "message": f"Failed to write block {block}", "readerstatus": "WRITE_FAILED"}
            finally:
                self.api.disconnect_tag()

            return {
                "status": True,
                "message": "Memory write successful",
                "readerstatus": "WRITE_SUCCESS"
            }

    def changesectorkey(self, uid, sector, current_key, new_key, keyB=None):
        """
        Safely change Key A and optionally Key B for a sector while preserving existing access bits.
        ONLY modifies sector trailer block - all normal data blocks remain untouched.
        :param uid: Card UID
        :param sector: Sector number (0-39: 0-31 for 4-block sectors, 32-39 for 16-block sectors)
        :param current_key: Current Key A to authenticate with
        :param new_key: New Key A to write
        :param keyB: Optional new Key B (if None, preserves existing Key B)
        """
        # Validate sector number
        if not isinstance(sector, int) or sector < 0 or sector > 39:
            return {"status": False, "message": "Sector must be 0-39", "readerstatus": "BAD_REQUEST"}
        
        with self._lock:
            self._check_connection()
            try:
                curr_key = self._normalize_key(current_key)
                n_key = self._normalize_key(new_key)
                key_b = self._normalize_key(keyB) if keyB is not None else None
            except Exception as e:
                return {"status": False, "message": str(e), "readerstatus": "BAD_REQUEST"}

            trailer_block = self._get_trailer_block_from_sector(sector)

            if not self.api.connect_tag(uid, 2):
                return {"status": False, "message": "Failed to connect to tag", "readerstatus": "CONNECT_FAILED"}

            try:
                # Authenticate with current key
                if not self.api.iso14443a_authenticate(trailer_block, 0, curr_key):
                    return {"status": False, "message": f"Authentication failed for sector {sector} with current key", "readerstatus": "AUTH_FAILED"}

                # Read existing trailer to preserve access bits and optionally Key B
                old_trailer = self.api.iso14443a_read_block(trailer_block)
                if not old_trailer or len(old_trailer) < 16:
                    return {"status": False, "message": f"Failed to read sector {sector} trailer block", "readerstatus": "READ_FAILED"}

                # Preserve existing access bits (bytes 6-10)
                access_bits = old_trailer[6:10]
                if key_b is None:
                    # Preserve existing Key B if not provided
                    key_b = old_trailer[10:16]

                # Build new trailer: Key A (6 bytes) + Access Bits (4 bytes) + Key B (6 bytes)
                new_trailer = list(n_key) + list(access_bits) + list(key_b)

                # Re-authenticate and write new trailer
                if not self.api.iso14443a_authenticate(trailer_block, 0, curr_key):
                    return {"status": False, "message": f"Re-authentication failed for sector {sector}", "readerstatus": "AUTH_FAILED"}
                
                if not self.api.iso14443a_write_block(trailer_block, new_trailer):
                    return {"status": False, "message": f"Failed to write sector {sector} trailer block", "readerstatus": "WRITE_FAILED"}
            finally:
                self.api.disconnect_tag()

            return {
                "status": True,
                "message": f"Sector {sector} key changed successfully (access bits preserved)",
                "readerstatus": "KEY_CHANGED"
            }
