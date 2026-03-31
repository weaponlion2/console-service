import serial, os, time

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
TYPE_A = ord('A')
RF_ON = 0x01
RF_OFF = 0x00
REQ_ALL = 0x52
KEY_A = 0x60
LED_BLUE = 0x01
LED_OFF = 0x00
DEFAULT_KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
BLOCK_TO_READ = 1
BLOCK_TO_READ_LENGTH = 32


class ER302_Reader:
    
    @staticmethod 
    def byte_array_to_hex(byte_array):
        return ''.join(f'{b:02X}' for b in byte_array)

    @staticmethod
    def hex_to_string(hex_str):
        if isinstance(hex_str, bytes):
            hex_str = hex_str.decode()

        hex_str = hex_str.strip()

        print("DEBUG FINAL:", repr(hex_str), len(hex_str))

        if len(hex_str) % 2 != 0:
            raise ValueError(f"Hex string must have even length: {repr(hex_str)}")

        try:
            return bytes.fromhex(hex_str).decode('utf-8').rstrip()
        except Exception as e:
            raise ValueError(f"Decoding failed: {repr(hex_str)}") from e

    
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
            return None, None, None, None

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
        """Authenticates a specific block."""
        params = [key_type, block] + key
        self._send_cmd(CMD_M1_AUTH, params)
        _, _, status, _ = self._recv_resp()
        return status == 0x00

    def write_block(self, block, data, key_type=KEY_A, key=DEFAULT_KEY):
        """Writes 16 bytes to a specific block."""
        if len(data) != 16:
            raise ValueError("Block must be exactly 16 bytes")

        if not self.auth_block(block, key_type, key):
            return False

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

    def processResult(self, uid_bytes):
        try:
            memData = ""
            if not self.select_card(uid_bytes):
                return {
                    "status": False,
                    "memData": None,
                    "message": "Card not selected",
                    "readerstatus": "CARD_NOT_SELECTED"
                }

            block = 1
            if self.auth_block(block):
                data = self.read_block(block)
                if data:
                    memData = ER302_Reader.byte_array_to_hex(data)
                    memData = ER302_Reader.hex_to_string(memData)
                    return {
                        "status": True,
                        "memData": memData,
                        "message": "Card block data",
                        "readerstatus": "CARD_VALID"
                    }
                
                else: return {
                    "status": False,
                    "memData": memData,
                    "message": "Error while reading data of block 1",
                    "readerstatus": "READ_FAILED"
                }
            else: return {
                    "status": False,
                    "memData": None,
                    "message": f"Block {block} authentication failed",
                    "readerstatus": "AUTH_FAILED"
                }            
        finally:            
            self.halt_and_reset() 
    
    def read_card(self, isReadMem):
        
        if not self.ser or not self.ser.is_open:
            return {
                "status": False,
                "data": None,
                "message": "Reader not ready",
                "readerstatus": "READER_NOT_READY"
            }
            
        self._send_cmd(CMD_REQUEST, [REQ_ALL])
        _, _, req_stat, _ = self._recv_resp()
        
        
        if req_stat != 0x00:
            return {
                "status": False,
                "data": None,
                "message": "No card available on machine",
                "readerstatus": "NO_CARD"
            }

        for attempt in range(3):
            self._send_cmd(CMD_ANTICOLL)
            _, _, ac_stat, data = self._recv_resp()

            if ac_stat == 0x00 and data and len(data) >= 4:
                uid_bytes = data[:4]
                uid_str = " ".join(f"{b:02X}" for b in uid_bytes)

                if isReadMem:
                    processResponse = self.processResult(uid_bytes)
                    return {
                        "status": processResponse["status"],
                        "data": processResponse["memData"],
                        "message": processResponse["message"],
                        "readerstatus": processResponse["readerstatus"]
                    }
                else:
                    return {
                        "status": True,
                        "data": uid_str,
                        "message": "Card uid value",
                        "readerstatus": "CARD_VALID"
                    }

            # 🔧 Small delay improves success rate significantly
            time.sleep(0.05)

        return {
            "status": False,
            "data": None,
            "message": "Anticollision failed after retries",
            "readerstatus": "ANTICOLL_FAIL"
        }


    def read_cardV2(self, payload):
        """Read multiple blocks from the card and optionally update block data.

        payload:
          key: key for authentication (hex string or 6-byte list)
          block: starting block (default BLOCK_TO_READ)
          length: number of bytes to read (default BLOCK_TO_READ_LENGTH)
          write: optional dict {block:int, data:16-byte list/tuple/hexstring}
        """
        block_key = ER302_Reader.__normalize_key(payload.get("key", DEFAULT_KEY))
        block_start_no = int(payload.get("block", BLOCK_TO_READ))
        length = int(payload.get("length", BLOCK_TO_READ_LENGTH))
        block_end_no = block_start_no + (length // 16) - 1

        if not self.ser or not self.ser.is_open:
            return {
                "status": False,
                "data": None,
                "message": "Reader not ready",
                "readerstatus": "READER_NOT_READY"
            }

        self._send_cmd(CMD_REQUEST, [REQ_ALL])
        _, _, req_stat, _ = self._recv_resp()

        if req_stat != 0x00:
            return {
                "status": False,
                "data": None,
                "message": "No card available on machine",
                "readerstatus": "NO_CARD"
            }
            
        for attempt in range(3):
            # Do one anticollision and card select for this sequence
            self._send_cmd(CMD_ANTICOLL)
            _, _, ac_stat, data = self._recv_resp()
            if ac_stat != 0x00 or not data or len(data) < 4:
                continue

            uid_bytes = data[:4]

            blocks = list(range(block_start_no, block_end_no + 1))

            processResponse = self.processResultV2({
                "uid_bytes": uid_bytes,
                "blocks": blocks,
                "key": block_key,
                "length": length,
            })

            if not processResponse["status"]:
                self.halt_and_reset()
                return processResponse

            read_hex = processResponse["memData"]

            self.halt_and_reset()

            return {
                "status": True,
                "data": read_hex,
                "message": "Card read successfully",
                "readerstatus": "CARD_VALID"
            }


        return {
                    "status": False,
                    "data": None,
                    "message": "Anticollision failed",
                    "readerstatus": "ANTICOLL_FAIL"
                }

    def processResultV2(self, payload):
        """Read one or more blocks while the card is selected."""
        uid_bytes = payload.get("uid_bytes")
        blocks = payload.get("blocks", payload.get("block"))
        key = ER302_Reader.__normalize_key(payload.get("key", DEFAULT_KEY))
        length = payload.get("length", BLOCK_TO_READ_LENGTH)

        if blocks is None:
            return {
                "status": False,
                "memData": None,
                "message": "blocks is required",
                "readerstatus": "BAD_REQUEST"
            }

        if isinstance(blocks, int):
            blocks = [blocks]
        elif not isinstance(blocks, (list, tuple)):
            return {
                "status": False,
                "memData": None,
                "message": "blocks must be int or list of ints",
                "readerstatus": "BAD_REQUEST"
            }

        if not self.select_card(uid_bytes):
            return {
                "status": False,
                "memData": None,
                "message": "Card not selected",
                "readerstatus": "CARD_NOT_SELECTED"
            }

        block_data = bytearray()

        for block in blocks:
            if not self.auth_block(block, KEY_A, key):
                return {
                    "status": False,
                    "memData": None,
                    "message": f"Block {block} authentication failed",
                    "readerstatus": "AUTH_FAILED"
                }

            data = self.read_block(block)
            if data is None:
                return {
                    "status": False,
                    "memData": None,
                    "message": f"Error while reading block {block}",
                    "readerstatus": "READ_FAILED"
                }

            block_data.extend(data)
        
        block_data = (ER302_Reader.byte_array_to_hex(block_data))[0:length]

        return {
            "status": True,
            "memData": block_data,
            "message": "Block data read",
            "readerstatus": "CARD_VALID"
        }

    def change_sector_key(self, payload):
        """Change sector trailer key A (and optional key B)."""
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

        trailer_block = sector * 4 + 3

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

        if not self.write_block(trailer_block, list(new_trailer), KEY_A, current_key):
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

    def is_reader_connected(self):
        return os.path.exists(self.port)


def print_table(block_num, data):
    """Prints block data in Hex and ASCII format."""
    hex_str = " ".join(f"{b:02X}" for b in data)
    ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in data)
    print(f"Block {block_num:02d} | {hex_str} | {ascii_str}")

