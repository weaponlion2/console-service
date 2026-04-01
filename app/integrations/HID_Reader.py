import asyncio
from fastapi import HTTPException 
from smartcard.System import readers
from smartcard.Exceptions import NoCardException, CardConnectionException
import time


# MIFARE default key and block
DEFAULT_KEY_A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
BLOCK_TO_READ = 0
USB_SLEEP_MILLIS = 0.2  # seconds
CARD_TIMEOUT = 20  # seconds max wait for card

class HID_Reader:    
    
    # --- APDU helpers ---
    
    @staticmethod
    def __generate_key(key_str):
        key_str = key_str.replace(" ", "")
        if len(key_str) != 12:
            raise ValueError("Key must be 12 hex characters (6 bytes)")
        return [int(key_str[i:i+2], 16) for i in range(0, 12, 2)]

    @staticmethod
    def __normalize_key(key):
        if isinstance(key, str):
            return HID_Reader.__generate_key(key)
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
        hex_str = hex_str.replace(" ", "")
        return bytes.fromhex(hex_str).decode('utf-8')

    
    @staticmethod
    def __load_key_apdu(key):
        return [0xFF, 0x82, 0x20, 0x00, 0x06, *key]

    @staticmethod
    def __auth_block_apdu(block):
        return [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, block, 0x60, 0x00]

    @staticmethod
    def __read_block_apdu(block):
        return [0xFF, 0xB0, 0x00, block, 0x10]

    @staticmethod
    def __is_success(resp):
        return len(resp) >= 2 and resp[-2] == 0x90 and resp[-1] == 0x00

    @staticmethod
    def __bytes_to_string(byte_array):
        return bytes(byte_array).decode('utf-8', errors='ignore').replace('\x00','').strip()

    @staticmethod
    def __get_uid(card):
        GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        resp, sw1, sw2 = card.transmit(GET_UID)
        if sw1 == 0x90 and sw2 == 0x00:
            return ''.join(f'{b:02X}' for b in resp)
        return None

    @staticmethod
    def __read_mifare_block(card, block, key_a=DEFAULT_KEY_A):
        try:
            if HID_Reader.is_trailer_block(block):
                return {
                    "status": False,
                    "data": None,
                    "message": f"Cannot read trailer block {block}",
                    "readerstatus": "BAD_REQUEST"
                }
            # print(f"Reading block {block} with key {key_a}")
            key_a = HID_Reader.__normalize_key(key_a)
            # --- Load Key ---
            resp, sw1, sw2 = card.transmit(HID_Reader.__load_key_apdu(key_a))
            if (sw1, sw2) != (0x90, 0x00):
                return {
                    "status": False,
                    "data": None,
                    "message": "Failed to load key",
                    "readerstatus": "KEY_LOAD_FAILED"
                }

            # --- Authenticate ---
            resp, sw1, sw2 = card.transmit(HID_Reader.__auth_block_apdu(block))
            if (sw1, sw2) != (0x90, 0x00):
                return {
                    "status": False,
                    "data": None,
                    "message": f"Failed to authenticate block {block}",
                    "readerstatus": "AUTH_FAILED"
                }

            # --- Read Block ---
            resp, sw1, sw2 = card.transmit(HID_Reader.__read_block_apdu(block))
            if (sw1, sw2) != (0x90, 0x00):
                return {
                    "status": False,
                    "data": None,
                    "message": f"Failed to read block {block}",
                    "readerstatus": "READ_FAILED"
                }

            return {
                "status": True,
                "data": resp,
                "message": "Block read successfully",
                "readerstatus": "READ_SUCCESS"
            }

        except Exception as e:
            return {
                "status": False,
                "data": None,
                "message": str(e),
                "readerstatus": "PROCESS_ERROR"
            }

    @staticmethod
    def __update_block_apdu(block, data):
        if len(data) != 16:
            raise ValueError("Block data must be exactly 16 bytes")
        return [0xFF, 0xD6, 0x00, block, 0x10, *data]

    @staticmethod
    def __write_mifare_block(card, block, data, key_a=DEFAULT_KEY_A):
        try:
            if HID_Reader.is_trailer_block(block):
                return {
                    "status": False,
                    "data": None,
                    "message": f"Cannot write trailer block {block}",
                    "readerstatus": "BAD_REQUEST"
                }
            key_a = HID_Reader.__normalize_key(key_a)

            # --- Load Key ---
            resp, sw1, sw2 = card.transmit(HID_Reader.__load_key_apdu(key_a))
            if (sw1, sw2) != (0x90, 0x00):
                return {
                    "status": False,
                    "data": None,
                    "message": "Failed to load key",
                    "readerstatus": "KEY_LOAD_FAILED"
                }

            # --- Authenticate ---
            resp, sw1, sw2 = card.transmit(HID_Reader.__auth_block_apdu(block))
            if (sw1, sw2) != (0x90, 0x00):
                return {
                    "status": False,
                    "data": None,
                    "message": f"Failed to authenticate block {block}",
                    "readerstatus": "AUTH_FAILED"
                }

            # --- Write Block ---
            resp, sw1, sw2 = card.transmit(HID_Reader.__update_block_apdu(block, data))
            if (sw1, sw2) != (0x90, 0x00):
                return {
                    "status": False,
                    "data": None,
                    "message": f"Failed to write block {block}",
                    "readerstatus": "WRITE_FAILED"
                }

            return {
                "status": True,
                "data": None,
                "message": "Block written successfully",
                "readerstatus": "WRITE_SUCCESS"
            }

        except Exception as e:
            return {
                "status": False,
                "data": None,
                "message": str(e),
                "readerstatus": "PROCESS_ERROR"
            }

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
    def is_trailer_block(block: int) -> bool:
        if block < 0 or block > 255:
            raise ValueError("Invalid block number")
        if block < 128:
            return block % 4 == 3
        return (block - 128) % 16 == 15

    @staticmethod
    def get_available_blocks(start_block: int, data_length: int):
        if start_block < 0 or start_block > 255:
            raise ValueError("Invalid block number")
        if data_length <= 0:
            return []

        blocks_needed = (data_length + 15) // 16
        blocks = []
        block = start_block

        while len(blocks) < blocks_needed and block <= 255:
            if not HID_Reader.is_trailer_block(block):
                blocks.append(block)
            block += 1

        if len(blocks) < blocks_needed:
            raise ValueError("Not enough blocks available to satisfy length")

        return blocks

# ---------------------------------------------------------------------------------------------------------- #

    def open(self):
        r = readers()

        if not r:
            return False

        target = "OMNIKEY"
        self.reader = next((x for x in r if target in str(x)), None)
        
        if self.reader: return True
        return False


    def change_sector_key(self, payload):
        try:
            if "current_key" not in payload or "new_key" not in payload:
                return {
                    "status": False,
                    "data": None,
                    "message": "current_key and new_key are required",
                    "readerstatus": "BAD_REQUEST"
                }

            sector = int(payload.get("sector", 0))
            if sector < 0:
                raise ValueError("Sector must be a non-negative integer")

            trailer_block = HID_Reader.get_trailer_block_from_sector(sector)

            current_key = HID_Reader.__normalize_key(payload["current_key"])
            new_key = HID_Reader.__normalize_key(payload["new_key"])

            connection = self.reader.createConnection()
            connection.connect()

            # authenticate using old key A for trailer
            auth_resp = self.__read_mifare_block(connection, trailer_block, current_key)
            if not auth_resp["status"]:
                return {
                    "status": False,
                    "data": None,
                    "message": f"Could not authenticate block with current key",
                    "readerstatus": auth_resp["readerstatus"]
                }

            trailer_bytes = auth_resp["data"]
            access_bytes = trailer_bytes[6:10]

            if "keyB" in payload and payload["keyB"] is not None:
                keyB = HID_Reader.__normalize_key(payload["keyB"])
            else:
                keyB = trailer_bytes[10:16]

            new_trailer = new_key + access_bytes + keyB

            resp, sw1, sw2 = connection.transmit(HID_Reader.__update_block_apdu(trailer_block, new_trailer))
            if not (sw1 == 0x90 and sw2 == 0x00):
                return {
                    "status": False,
                    "data": None,
                    "message": f"Failed to write new key to trailer block {trailer_block}",
                    "readerstatus": "KEY_CHANGE_FAILED"
                }

            return {
                "status": True,
                "data": None,
                "message": "Block key changed successfully",
                "readerstatus": "KEY_CHANGED"
            }
        except NoCardException:
            return {
                "status": False,
                "data": None,
                "message": "No card detected",
                "readerstatus": "NO_CARD"
            }
        except Exception as e:
            return {
                "status": False,
                "data": None,
                "message": str(e),
                "readerstatus": "PROCESS_ERROR"
            }

    def read_memory(self, payload):
        try:
            block_key = HID_Reader.__normalize_key(payload.get("key", DEFAULT_KEY_A))
            block_start_no = int(payload.get("block", BLOCK_TO_READ))
            length = int(payload.get("length", 32))
            if length <= 0:
                return {
                    "status": False,
                    "data": None,
                    "message": "length must be positive",
                    "readerstatus": "BAD_REQUEST"
                }
            blocks_needed = (length + 15) // 16
            block_end_no = block_start_no + blocks_needed - 1
            if block_start_no < 0 or block_end_no > 255:
                return {
                    "status": False,
                    "data": None,
                    "message": "Block range out of bounds",
                    "readerstatus": "BAD_REQUEST"
                }

            connection = self.reader.createConnection()
            connection.connect()

            # --- Read Block (UPDATED HANDLING) ---
            block_data = bytearray()
            try:
                blocks = HID_Reader.get_available_blocks(block_start_no, length)
            except ValueError as e:
                return {
                    "status": False,
                    "data": None,
                    "message": str(e),
                    "readerstatus": "BAD_REQUEST"
                }

            for block in blocks:
                read_resp = self.__read_mifare_block(connection, block, block_key)
                if not read_resp["status"]:
                    return {
                        "status": False,
                        "data": None,
                        "message": read_resp["message"],
                        "readerstatus": read_resp["readerstatus"]
                    }
                block_data.extend(read_resp["data"]) 
            
            # print(f"Full block data before trimming: {block_data}")

            block_data = HID_Reader.byte_array_to_hex(block_data)[: length * 2]

            return {
                "status": True,
                "data": block_data,
                "message": "Card read successfully",
                "readerstatus": "CARD_VALID"
            }

        except NoCardException as e:
            return {
                "status": False,
                "data": None,
                "message": "No card detected",
                "readerstatus": "NO_CARD"
            }

    def read_uid(self):
        try:
            connection = self.reader.createConnection()
            connection.connect()

            uid = self.__get_uid(connection)

            return {
                "status": True if uid else False,
                "data": uid if uid else None,
                "message": "Card UID read successfully" if uid else "Failed to get UID",
                "readerstatus": "CARD_VALID" if uid else "UID_FAILED"
            }

        except NoCardException as e:
            return {
                "status": False,
                "data": None,
                "message": "No card detected",
                "readerstatus": "NO_CARD"
            }

    def write_memory(self, payload):
        try:
            block_key = HID_Reader.__normalize_key(payload.get("key", DEFAULT_KEY_A))
            block_start_no = int(payload.get("block", BLOCK_TO_READ))
            data_payload = payload.get("data")

            if not data_payload:
                return {
                    "status": False,
                    "data": None,
                    "message": "data is required",
                    "readerstatus": "BAD_REQUEST"
                }

            connection = self.reader.createConnection()
            connection.connect()

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

            for block, block_data in sorted(to_write.items()):
                if block < 0 or block > 255:
                    return {
                        "status": False,
                        "data": None,
                        "message": f"Invalid block number: {block}",
                        "readerstatus": "BAD_REQUEST"
                    }

                if HID_Reader.is_trailer_block(block):
                    return {
                        "status": False,
                        "data": None,
                        "message": f"Cannot write trailer block {block}",
                        "readerstatus": "BAD_REQUEST"
                    }

                if len(block_data) != 16:
                    return {
                        "status": False,
                        "data": None,
                        "message": f"Internal error: block {block} length {len(block_data)} must be 16",
                        "readerstatus": "PROCESS_ERROR"
                    }

                write_resp = self.__write_mifare_block(connection, block, block_data, block_key)
                if not write_resp["status"]:
                    return {
                        "status": False,
                        "data": None,
                        "message": write_resp["message"],
                        "readerstatus": write_resp["readerstatus"]
                    }

            return {
                "status": True,
                "data": None,
                "message": "Memory write successful",
                "readerstatus": "WRITE_SUCCESS"
            }

        except NoCardException:
            return {
                "status": False,
                "data": None,
                "message": "No card detected",
                "readerstatus": "NO_CARD"
            }

        except Exception as e:
            return {
                "status": False,
                "data": None,
                "message": str(e),
                "readerstatus": "PROCESS_ERROR"
            }