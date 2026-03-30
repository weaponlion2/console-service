import asyncio
from fastapi import HTTPException 
from smartcard.System import readers
from smartcard.Exceptions import NoCardException, CardConnectionException
import time


# MIFARE default key and block
DEFAULT_KEY_A = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
BLOCK_TO_READ = 1
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

    def read_card(self, isReadMem):
        try:
            
            connection = self.reader.createConnection()
            connection.connect()

            # --- Get UID ---
            uid = self.__get_uid(connection)
            if not uid:
                return {
                    "status": False,
                    "data": None,
                    "message": "Failed to get UID",
                    "readerstatus": "UID_FAILED"
                    }           

            # --- UID Only Mode ---
            if not isReadMem:
                return {
                    "status": True,
                    "data": uid,
                    "message": "Card UID read successfully",
                    "readerstatus": "CARD_VALID"
                }

            # --- Read Block (UPDATED HANDLING) ---
            read_resp = self.__read_mifare_block(connection, BLOCK_TO_READ)

            if not read_resp["status"]:
                return {
                    "status": False,
                    "data": None,
                    "message": read_resp["message"],
                    "readerstatus": read_resp["readerstatus"]
                }

            block_data = self.__bytes_to_string(read_resp["data"])

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


    def read_cardV2(self, payload):
        try:
            block_key = HID_Reader.__generate_key(payload.get("key", DEFAULT_KEY_A))
            block_start_no = payload.get("block", BLOCK_TO_READ)
            length = payload.get("length", 32)
            block_end_no = block_start_no + (length // 16) - 1

            connection = self.reader.createConnection()
            connection.connect()

            # --- Read Block (UPDATED HANDLING) ---
            block_data = bytearray()
            for block in range(block_start_no, block_end_no + 1):
                read_resp = self.__read_mifare_block(connection, block, block_key)
                if not read_resp["status"]:
                    return {
                        "status": False,
                        "data": None,
                        "message": read_resp["message"],
                        "readerstatus": read_resp["readerstatus"]
                    }
                block_data.extend(read_resp["data"])
                print(f"Read block {block}: {read_resp['data']}")

            block_data = HID_Reader.byte_array_to_hex(block_data)[0:length]

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


    def open(self):
        r = readers()

        if not r:
            return False

        target = "OMNIKEY"
        self.reader = next((x for x in r if target in str(x)), None)
        
        if self.reader: return True
        return False

            

# --- API endpoint ---
# @app.get("/read-card", response_model=CardResponse)
# async def read_card():
#     uid, block_data = await wait_for_card()
#     return CardResponse(uid=uid, block_data=block_data)

# @app.get("/reader-health")
# async def reader_health():
#     r = readers()
#     if len(r) == 0:
#         raise HTTPException(status_code=500, detail="No smart card readers found")
#     return {"status": "Reader is connected"}
   