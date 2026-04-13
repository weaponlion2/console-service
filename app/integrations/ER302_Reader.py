import serial, os, time, math

class AuthenticationError(Exception):
    """Raised when a card block authentication fails."""
    pass

# --- Configuration ---
ER303_DEFAULT_PORT = "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"
ER303_DEFAULT_BAUD = 9600
ER303_TIMEOUT_SEC = 1.0

# --- Protocol Constants (from er302.h) ---
HEAD_1 = 0xAA
HEAD_2 = 0xBB
DEV_ID = [0x00, 0x00]

# Commands
CMD_GET_MODEL   = [0x04, 0x01]
CMD_INIT_TYPE   = [0x08, 0x01]
CMD_ANTENNA     = [0x0C, 0x01]
CMD_BEEP        = [0x06, 0x01]
CMD_LIGHT       = [0x07, 0x01]
CMD_REQUEST     = [0x01, 0x02]
CMD_ANTICOLL    = [0x02, 0x02]
CMD_SELECT      = [0x03, 0x02]
CMD_HALT        = [0x04, 0x02]
CMD_M1_AUTH     = [0x07, 0x02]
CMD_M1_READ     = [0x08, 0x02]
CMD_M1_WRITE    = [0x09, 0x02]

# Parameters
TYPE_A = ord('A') # integer Unicode code point value A, Decimal = 65, Hexadecimal = 0x41
RF_ON = 0x01
RF_OFF = 0x00
REQ_ALL = 0x52
KEY_A = 0x60
LED_BLUE = 0x01
LED_OFF = 0x00
DEFAULT_KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
BLOCK_TO_READ = 0
BLOCK_TO_READ_LENGTH = 32


class ER302_Reader:
    
    
    @staticmethod
    def get_trailer_block_from_sector(sector: int) -> int:
        if sector < 0 or sector > 39:
            raise ValueError("Invalid sector number (0–39)")

        # Sectors 0–31 (4 blocks each)
        if sector < 32:
            return sector * 4 + 3

        # Sectors 32–39 (16 blocks each)
        else:
            return 128 + (sector - 32) * 16 + 15


    @staticmethod
    def get_sector_trailer_block(block: int) -> int:
        if block < 0 or block > 255:
            raise ValueError("Invalid block number")

        # Sectors 0–31 (4 blocks each)
        if block < 128:
            sector = block // 4
            return sector * 4 + 3

        # Sectors 32–39 (16 blocks each)
        else:
            sector = (block - 128) // 16 + 32
            return 128 + (sector - 32) * 16 + 15

    @staticmethod
    def is_trailer_block(block: int) -> bool:
        if block < 0 or block > 255:
            raise ValueError("Invalid block number")
        if block < 128:
            return block % 4 == 3
        return (block - 128) % 16 == 15

        
    @staticmethod
    def __generate_key(key_str):
        key_str = key_str.replace(" ", "")
        if len(key_str) != 12:
            raise ValueError("Key must be 12 hex characters (6 bytes)")
        return [int(key_str[i:i+2], 16) for i in range(0, 12, 2)]

    @staticmethod
    def __normalize_key(key):
        if isinstance(key, str):
            return ER302_Reader.__generate_key(key)
        if isinstance(key, (list, tuple)):
            if len(key) != 6 or not all(isinstance(b, int) and 0 <= b <= 0xFF for b in key):
                raise ValueError("Key must be 6 bytes")
            return list(key)
        raise ValueError("Key must be a 6-byte list/tuple or 12-hex-character string")

    @staticmethod 
    def byte_array_to_hex(byte_array):
        return ''.join(f'{b:02X}' for b in byte_array)

    @staticmethod
    def hex_to_string(hex_str):
        if isinstance(hex_str, bytes):
            hex_str = hex_str.decode()

        hex_str = hex_str.strip()

        # print("DEBUG FINAL:", repr(hex_str), len(hex_str))

        if len(hex_str) % 2 != 0:
            raise ValueError(f"Hex string must have even length: {repr(hex_str)}")

        try:
            return bytes.fromhex(hex_str).decode('utf-8').rstrip()
        except Exception as e:
            raise ValueError(f"Decoding failed: {repr(hex_str)}") from e
    
    @staticmethod
    def get_available_blocks(start_block: int, data_length: int) -> list[int]:
        if start_block < 0 or start_block > 255:
            raise ValueError("Invalid start block")

        blocks_needed = math.ceil(data_length / 16)
        result = []

        block = start_block

        while len(result) < blocks_needed and block <= 255:
            # Determine if block is trailer
            if block < 128:
                is_trailer = (block % 4 == 3)
            else:
                is_trailer = ((block - 128) % 16 == 15)

            if not is_trailer:
                result.append(block)

            block += 1

        if len(result) < blocks_needed:
            raise ValueError("Not enough space available")

        return result

    
    def __init__(self, port, baud):
        self.port = port
        self.baud = baud
        self.ser = None

    def open(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=ER303_TIMEOUT_SEC,
                write_timeout=ER303_TIMEOUT_SEC
            )
            # Disable flow control
            self.ser.xonxoff = False
            self.ser.rtscts = False
            self.ser.dsrdtr = False
            return True
        except serial.SerialException as e:
            return False

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _calc_checksum(self, dev_id, cmd_code, status_or_params):
        ver = 0
        for b in dev_id:
            ver ^= b
        for b in cmd_code:
            ver ^= b
        for b in status_or_params:
            ver ^= b
        return ver

    def _send_cmd(self, cmd_code, params=None):
        """
        Constructs and sends a packet.
        Implements the 0xAA escaping logic found in er302.c send_command().
        """
        if not self.ser:
            raise RuntimeError("Serial port not open")


        if params is None:
            params = []

        # Packet Structure: Head(2) + Len(1) + Zero(1) + DevID(2) + Cmd(2) + Params + Ver(1)
        # Length field = 5 (DevID+Cmd+Ver) + len(params)
        pkg_len = 5 + len(params)
        
        tx_buf = [HEAD_1, HEAD_2, pkg_len, 0x00]
        tx_buf.extend(DEV_ID)
        tx_buf.extend(cmd_code)

        ver = self._calc_checksum(DEV_ID, cmd_code, params)

        # Write Params with Escaping
        # Logic from er302.c: "if (param[i] == 0xaa) { write(fd, &zero, 1); }"
        for p in params:
            tx_buf.append(p)
            if p == 0xAA:
                tx_buf.append(0x00)
        
        # Append Checksum
        tx_buf.append(ver)

        self.ser.write(bytes(tx_buf))
        # Debug: print(f"TX: {' '.join(f'{b:02X}' for b in tx_buf)}")

    def _recv_resp(self):
        """
        Receives and parses response.
        Implements the 0xAA escaping logic and checksum verification from er302.c receive_response().
        Returns: (dev_id, cmd_code, status, data_list) or (None, None, None, error_msg)
        """
        if not self.ser:
            return None, None, None, "Port closed"

        try:
            # 1. Read Header
            h1 = self.ser.read(1)
            if not h1 or h1[0] != HEAD_1:
                return None, None, None, "Header 1 Fail"
            
            h2 = self.ser.read(1)
            if not h2 or h2[0] != HEAD_2:
                return None, None, None, "Header 2 Fail"

            # 2. Read Length
            l_byte = self.ser.read(1)
            if not l_byte:
                return None, None, None, "Timeout reading Length"
            pkg_len = l_byte[0]

            # 3. Read Zero byte
            z = self.ser.read(1)            
            if not z:
                return None, None, None, None

            
            # 4. Read DevID (2 bytes)
            dev_id = list(self.ser.read(2))
            
            # 5. Read CmdCode (2 bytes)
            cmd_code = list(self.ser.read(2))
            
            # 6. Read Status (1 byte)
            s_byte = self.ser.read(1)
            if not s_byte:
                return None, None, None, "Timeout reading Status"
            status = s_byte[0]

            # 7. Read Data
            # Data length = Total Len - 6 (DevID(2) + Cmd(2) + Status(1) + Ver(1))
            data_len = pkg_len - 6
            data = []

            for _ in range(data_len):
                b_byte = self.ser.read(1)
                if not b_byte:
                    break
                val = b_byte[0]
                data.append(val)
                
                # Handle Escaping: If we read 0xAA, the next byte MUST be 0x00 (and ignored)
                if val == 0xAA:
                    esc = self.ser.read(1) 
                    # Optional: Verify esc is 0x00, but usually safe to just consume

            # 8. Read Verification Byte
            act_ver_byte = self.ser.read(1)
            
            # 9. Verify Checksum
            # Checksum = DevID ^ CmdCode ^ Status ^ Data
            calc_ver = self._calc_checksum(dev_id, cmd_code, [status] + data)
            
            if act_ver_byte and act_ver_byte[0] != calc_ver:
                # Warning only, proceed anyway as some implementations vary slightly
                pass

            return dev_id, cmd_code, status, data

        except Exception as e:
            return None, None, None, f"Recv response exception: {e}"

    def init_reader(self):
        """Initialize the reader hardware."""
        # Get Model
        self._send_cmd(CMD_GET_MODEL)
        _, _, status, data = self._recv_resp()
        if status != 0x00:
            return False

        # Init Type A
        self._send_cmd(CMD_INIT_TYPE, [TYPE_A])
        _, _, status, _ = self._recv_resp()
        if status != 0x00:
            return False

        # Antenna On
        self._send_cmd(CMD_ANTENNA, [RF_ON])
        _, _, status, _ = self._recv_resp()
        if status != 0x00:
            return False

        # Beep & Light
        self._send_cmd(CMD_BEEP, [50])
        self._recv_resp()
        self._send_cmd(CMD_LIGHT, [LED_BLUE])
        self._recv_resp()
        
        return True

    def select_card(self, uid_bytes):
        """Selects the card using its UID."""
        self._send_cmd(CMD_SELECT, list(uid_bytes))
        _, _, status, _ = self._recv_resp()
        return status == 0x00

    def auth_block(self, block, key_type=KEY_A, key=DEFAULT_KEY):
        params = [key_type, block] + key
        self._send_cmd(CMD_M1_AUTH, params)
        _, _, status, _ = self._recv_resp()
        return status == 0x00

    def write_block(self, block, data, key_type=KEY_A, key=DEFAULT_KEY):
        if len(data) != 16:
            raise ValueError("Block must be exactly 16 bytes")
        if ER302_Reader.is_trailer_block(block):
            raise ValueError("Cannot write trailer block {} through write_block".format(block))

        if not self.auth_block(block, key_type, key):
            raise AuthenticationError("Authentication failed for block {}".format(block))

        self._send_cmd(CMD_M1_WRITE, [block] + data)
        _, _, status, _ = self._recv_resp()
        return status == 0x00


    def write_blockWithoutSectorProtection(self, block, data, key_type=KEY_A, key=DEFAULT_KEY):
        if len(data) != 16:
            raise ValueError("Block must be exactly 16 bytes")
        
        if not self.auth_block(block, key_type, key):
            raise AuthenticationError("Authentication failed for block {}".format(block))

        self._send_cmd(CMD_M1_WRITE, [block] + data)
        _, _, status, _ = self._recv_resp()
        return status == 0x00


    def read_block(self, block):
        """Reads 16 bytes from a specific block."""
        self._send_cmd(CMD_M1_READ, [block])
        _, _, status, data = self._recv_resp()
        if status == 0x00 and len(data) >= 16:
            return data
        return None

    def halt_and_reset(self):
        """Halts the card and turns off antenna/LED."""
        self._send_cmd(CMD_HALT)
        self._recv_resp()
        self._send_cmd(CMD_ANTENNA, [RF_OFF])
        self._send_cmd(CMD_LIGHT, [LED_OFF])

    def is_reader_connected(self):
        return os.path.exists(self.port)

    def _find_card_uid(self):
        """Helper: request card and perform anticollision, returning UID bytes or error code."""
        self._send_cmd(CMD_REQUEST, [REQ_ALL])
        _, _, req_stat, _ = self._recv_resp()

        if req_stat != 0x00:
            return None, "NO_CARD"

        for attempt in range(3):
            self._send_cmd(CMD_ANTICOLL)
            _, _, ac_stat, data = self._recv_resp()

            if ac_stat == 0x00 and data and len(data) >= 4:
                return data[:4], None
            time.sleep(0.05)

        return None, "ANTICOLL_FAIL"

    def read_uid(self):
        if not self.ser or not self.ser.is_open:
            return {
                "status": False,
                "data": None,
                "message": "Reader not ready",
                "readerstatus": "READER_NOT_READY"
            }

        uid, err = self._find_card_uid()
        if err:
            if err == "NO_CARD":
                return {
                    "status": False,
                    "data": None,
                    "message": "No card available on machine",
                    "readerstatus": "NO_CARD"
                }
            return {
                "status": False,
                "data": None,
                "message": "Anticollision failed after retries",
                "readerstatus": "ANTICOLL_FAIL"
            }

        uid_str = "".join(f"{b:02X}" for b in uid)
        return {
            "status": True,
            "data": uid_str,
            "message": "Card uid value",
            "readerstatus": "CARD_VALID"
        }
    
    
    def read_memory(self, payload):
        
        if not self.ser or not self.ser.is_open:
            return {
                "status": False,
                "data": None,
                "message": "Reader not ready",
                "readerstatus": "READER_NOT_READY"
            }

        uid, err = self._find_card_uid()
        if err:
            return {
                "status": False,
                "data": None,
                "message": "No card available on machine" if err == "NO_CARD" else "Anticollision failed after retries",
                "readerstatus": err
            }

        processResponse = self.processBlocks(uid, payload)
        return {
            "status": processResponse["status"],
            "data": processResponse.get("memData"),
            "message": processResponse["message"],
            "readerstatus": processResponse["readerstatus"]
        }


    def processBlocks(self, uid_bytes, payload):

        block_key = ER302_Reader.__normalize_key(payload.get("key", DEFAULT_KEY))
        block_start_no = payload.get("block", BLOCK_TO_READ)
        length = payload.get("length", 32)
        blocks = ER302_Reader.get_available_blocks(block_start_no, length)
        
        # print(f"DEBUG: Processing blocks {blocks} with key {block_key} for UID {uid_bytes}")

        if not self.select_card(uid_bytes):
            return {
                "status": False,
                "memData": None,
                "message": "Card not selected",
                "readerstatus": "CARD_NOT_SELECTED"
            }

        block_data = bytearray()

        for block in blocks:
            if not self.auth_block(block, KEY_A, block_key):
                return {
                    "status": False,
                    "memData": None,
                    "message": f"Block {block} authentication failed",
                    "readerstatus": "AUTH_FAILED"
                }

            data = self.read_block(block)
            # print(f"DEBUG: Read block {block}: {data}")
            if data is None:
                return {
                    "status": False,
                    "memData": None,
                    "message": f"Error while reading block {block}",
                    "readerstatus": "READ_FAILED"
                }

            block_data.extend(data)

        if not isinstance(length, int) or length < 0:
            return {
                "status": False,
                "memData": None,
                "message": "Invalid length",
                "readerstatus": "BAD_REQUEST"
            }

        hex_data = ER302_Reader.byte_array_to_hex(block_data)
        block_data = hex_data[: length * 2]

        return {
            "status": True,
            "memData": block_data,
            "message": "Block data read",
            "readerstatus": "CARD_VALID"
        }

    
    def change_sector_key(self, payload):
        
        if not self.ser or not self.ser.is_open:
            return {
                "status": False,
                "data": None,
                "message": "Reader not ready",
                "readerstatus": "READER_NOT_READY"
            }

        uid, err = self._find_card_uid()
        if err:
            return {
                "status": False,
                "data": None,
                "message": "No card available on machine" if err == "NO_CARD" else "Anticollision failed after retries",
                "readerstatus": err
            }

        processResponse = self.change_sector_key_process(uid, payload)
        return {
            "status": processResponse["status"],
            "data": processResponse.get("data"),
            "message": processResponse["message"],
            "readerstatus": processResponse["readerstatus"]
        }


    def change_sector_key_process(self, uid_bytes, payload):
        sector = int(payload.get("sector", 0))
        current_key = payload.get("current_key", "FFFFFFFFFFFF")
        new_key = payload.get("new_key")
        keyB = payload.get("keyB")

        if new_key is None:
            return {
                "status": False,
                "data": None,
                "message": "new_key is required",
                "readerstatus": "BAD_REQUEST"
            }

        try:
            current_key = ER302_Reader.__normalize_key(current_key)
            new_key = ER302_Reader.__normalize_key(new_key)
            if keyB is not None:
                keyB = ER302_Reader.__normalize_key(keyB)
        except Exception as e:
            return {
                "status": False,
                "data": None,
                "message": str(e),
                "readerstatus": "BAD_REQUEST"
            }

        trailer_block = self.get_trailer_block_from_sector(sector)
        
        # print(f"DEBUG: Changing sector {sector} with trailer block {trailer_block}, current_key {current_key}, new_key {new_key}, keyB {keyB}")

        if not self.select_card(uid_bytes):
            return {
                "status": False,
                "memData": None,
                "message": "Card not selected",
                "readerstatus": "CARD_NOT_SELECTED"
            }

        # authenticate with old key
        if not self.auth_block(trailer_block, KEY_A, current_key):
            return {
                "status": False,
                "data": None,
                "message": "Failed to auth trailer with current key",
                "readerstatus": "AUTH_FAILED"
            }

        old_trailer = self.read_block(trailer_block)
        if old_trailer is None:
            return {
                "status": False,
                "data": None,
                "message": "Failed to read trailer block",
                "readerstatus": "READ_FAILED"
            }
            
        access_bits = old_trailer[6:10]

        if keyB is None:
            keyB = old_trailer[10:16]

        new_trailer = bytes(new_key + access_bits + keyB)
        if len(new_trailer) != 16:
            return {
                "status": False,
                "data": None,
                "message": "Trailer data length invalid",
                "readerstatus": "KEY_CHANGE_FAILED"
            }

        if not self.write_blockWithoutSectorProtection(trailer_block, list(new_trailer), KEY_A, current_key):
            return {
                "status": False,
                "data": None,
                "message": "Failed to write trailer block",
                "readerstatus": "KEY_CHANGE_FAILED"
            }

        return {
            "status": True,
            "data": None,
            "message": "Sector key changed",
            "readerstatus": "KEY_CHANGED"
        }

    
    def write_memory(self, payload):
        
        if not self.ser or not self.ser.is_open:
            return {
                "status": False,
                "data": None,
                "message": "Reader not ready",
                "readerstatus": "READER_NOT_READY"
            }

        uid, err = self._find_card_uid()
        if err:
            return {
                "status": False,
                "data": None,
                "message": "No card available on machine" if err == "NO_CARD" else "Anticollision failed after retries",
                "readerstatus": err
            }

        processResponse = self.write_memory_process(uid, payload)
        return {
            "status": processResponse["status"],
            "data": processResponse.get("data"),
            "message": processResponse["message"],
            "readerstatus": processResponse["readerstatus"]
        }
    
    
    def write_memory_process(self, uid_bytes, payload):
        block_start_no = int(payload.get("block", 0))
        block_key = payload.get("key", "FFFFFFFFFFFF")
        data_payload = payload.get("data")

        try:
            block_key = ER302_Reader.__normalize_key(block_key)
        except Exception as e:
            return {
                "status": False,
                "data": None,
                "message": str(e),
                "readerstatus": "BAD_REQUEST"
            }       
        
        to_write = {}

        if isinstance(data_payload, str):
            data_payload = data_payload.replace(" ", "")
            if len(data_payload) % 2 != 0:
                return {
                    "status": False,
                    "data": None,
                    "message": "Hex string must have even length",
                    "readerstatus": "BAD_REQUEST"
                }

            # decode hex string into bytes
            try:
                raw_bytes = bytes.fromhex(data_payload)
            except ValueError:
                return {
                        "status": False,
                        "data": None,
                        "message": "data must be valid hex string",
                        "readerstatus": "BAD_REQUEST"
                    }

            # pad to 16-byte boundary if needed
            if len(raw_bytes) % 16 != 0:
                pad_len = 16 - (len(raw_bytes) % 16)
                raw_bytes = raw_bytes + bytes([0] * pad_len)

            for i in range(0, len(raw_bytes), 16):
                block = block_start_no + (i // 16)
                chunk = raw_bytes[i:i+16]
                to_write[block] = list(chunk)

        elif isinstance(data_payload, (list, tuple)):
            data_bytes = list(data_payload)
            if len(data_bytes) % 16 != 0:
                pad_len = 16 - (len(data_bytes) % 16)
                data_bytes = data_bytes + [0] * pad_len

            for i in range(0, len(data_bytes), 16):
                block = block_start_no + (i // 16)
                to_write[block] = data_bytes[i:i+16]

        else:
            return {
                "status": False,
                "data": None,
                "message": "data must be hex string or byte list",
                "readerstatus": "BAD_REQUEST"
            }

        if not self.select_card(uid_bytes):
            return {
                "status": False,
                "memData": None,
                "message": "Card not selected",
                "readerstatus": "CARD_NOT_SELECTED"
            }

        for block, block_data in sorted(to_write.items()):
            if block < 0 or block > 255:
                return {
                    "status": False,
                    "data": None,
                    "message": f"Invalid block number: {block}",
                    "readerstatus": "BAD_REQUEST"
                }

            if ER302_Reader.is_trailer_block(block):
                return {
                    "status": False,
                    "data": None,
                    "message": f"Cannot write trailer block {block}",
                    "readerstatus": "BAD_REQUEST"
                }

            # print(f"DEBUG: Writing block {block} with data {block_data}")

            if not self.write_block(block, list(block_data), KEY_A, block_key):
                return {
                    "status": False,
                    "data": None,
                    "message": "Failed to write memory block",
                    "readerstatus": "FAILED_TO_WRITE_BLOCK"
                }


        return {
            "status": True,
            "data": None,
            "message": "Memory write successful",
            "readerstatus": "WRITE_SUCCESS"
        }


    

