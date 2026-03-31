from app.schemas.card import PatronRequest as ReaderRequest
from app.integrations.ER302_Reader import ER302_Reader, ER303_TIMEOUT_SEC, ER303_DEFAULT_BAUD, ER303_DEFAULT_PORT
from app.integrations.HID_Reader import HID_Reader

ReaderList = {
    "CELRDR": "CELRDR",
    "HIDOK": "HIDOK"
}


class ReaderClient:
    hidReader = None
    er302Reader = None
            
    
    def __isReaderValid(self, readerType):
        return {
            ReaderList["CELRDR"]: True,
            ReaderList["HIDOK"]: True,
        }.get(readerType, False)

    
    def __create_er302_reader(self):
        reader = ER302_Reader(ER303_DEFAULT_PORT, ER303_DEFAULT_BAUD)
        if not reader.open():
            return self.__fail("ER302 Reader not connected", "NO_READER")

        if not reader.init_reader():
            return self.__fail("ER302 Reader init failed", "NOT_CONNECTED")

        self.er302Reader = reader
        self.hidReader = None
        return self.__success(reader, "ER302 Reader connected")


    def __create_hid_reader(self):
        reader = HID_Reader()
        if not reader.open():
            return self.__fail("HID Reader not connected", "NOT_CONNECTED")

        self.hidReader = reader
        self.er302Reader = None
        return self.__success(reader, "Hid Reader connected")


    def __success(self, reader, message):
        return {
            "status": True,
            "reader": reader,
            "message": message,
            "readerstatus": "READER_CONNECTED"
        }


    def __fail(self, message, code):
        return {
            "status": False,
            "reader": None,
            "message": message,
            "readerstatus": code
        }


    def __get_reader(self, payload: ReaderRequest):
        reader_type = payload.get("reader")

        if not self.__isReaderValid(reader_type):
            return self.__fail("Invalid reader type", "READER_INVALID")

        if reader_type == ReaderList["CELRDR"]:
            return self.er302Reader and self.__success(self.er302Reader, "ER302 Reader connected") \
                or self.__create_er302_reader()

        if reader_type == ReaderList["HIDOK"]:
            return self.hidReader and self.__success(self.hidReader, "Hid Reader connected") \
                or self.__create_hid_reader()

        return self.__fail("Unsupported reader", "READER_INVALID")

    
    def readMemory(self, payload: ReaderRequest):
        reader = self.__current_reader(payload)
        # print(f"Reading memory with reader: {reader}, payload: {payload}")

        if isinstance(reader, dict):
            return reader

        try:
            response = reader.read_memory(payload)

            return {
                "status": "success" if response["status"] is True else "fail",
                "readerstatus": response["readerstatus"],
                "message": response["message"],
                "output": response["data"] if response["status"] is True else None
            }

        except Exception as e:
            print(f"Error in readUID: {e}")
            return {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e),
                "output": None
            }

    
    def writeMemory(self, payload: ReaderRequest):
        # writeMemory uses read_cardV2 path and accepts payload['write'] ({block:hexstring/list})
        return self.readMemory(payload)

    def changeBlockKey(self, payload: ReaderRequest):
        reader = self.__current_reader(payload)
        print(f"Changing block key with reader: {reader}, payload: {payload}")

        if isinstance(reader, dict):
            return reader

        try:
            if hasattr(reader, 'change_block_key'):
                cardResponse = reader.change_block_key(payload)
            else:
                return {
                    "status": "fail",
                    "readerstatus": "NO_SECURE_SUPPORT",
                    "message": "Secure block change not supported by this reader",
                    "output": None
                }

            if cardResponse.get("status") is True:
                return {
                    "status": "success",
                    "readerstatus": cardResponse.get("readerstatus", "KEY_CHANGED"),
                    "message": cardResponse.get("message", "Key updated"),
                    "output": cardResponse.get("data")
                }
            else:
                return {
                    "status": "fail",
                    "readerstatus": cardResponse.get("readerstatus", "KEY_CHANGE_FAILED"),
                    "message": cardResponse.get("message", "Key update failed"),
                    "output": None
                }

        except Exception as e:
            print(f"Error in ReaderClient.secureBlock: {e}")
            return {
                    "status": "fail",
                    "readerstatus": "PROCESS_ERROR",
                    "message": str(e),
                    "output": None
                }
    
    
    def readUID(self, payload: ReaderRequest):
        reader = self.__current_reader(payload)

        if isinstance(reader, dict):
            return reader

        try:
            response = reader.read_uid()

            return {
                "status": "success" if response["status"] else "fail",
                "readerstatus": response["readerstatus"],
                "message": response["message"],
                "output": response["data"] if response["status"] else None
            }

        except Exception as e:
            print(f"Error in readUID: {e}")
            return {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e),
                "output": None
            }

    
    def __current_reader(self, payload):
        try:
            response = self.__get_reader(payload)

            if not response["status"]:
                return {
                    "status": "fail",
                    "readerstatus": response["readerstatus"],
                    "message": response["message"],
                    "output": None
                }

            return response["reader"]

        except Exception as e:
            print(f"Error in __current_reader: {e}")
            self.er302Reader = None
            self.hidReader = None

            return {
                "status": "fail",
                "readerstatus": "NO_READER",
                "message": str(e),
                "output": None
            }

            
            