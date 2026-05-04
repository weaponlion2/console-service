import sys
from app.schemas.card import InternalPatronRequest as ReaderRequest, MemoryUpdateRequest
from app.integrations.ER302_Reader import ER302_Reader, ER303_DEFAULT_BAUD, ER303_DEFAULT_PORT
from app.integrations.HID_Reader import HID_Reader
from app.utils.detect_port import find_cp2102

ReaderList = {
    "CELRDR": "CELRDR",
    "HIDOK": "HIDOK"
}


class ReaderClient:
    hidReader = None
    er302Reader = None
    reader = None
    reader_type = None
            
    
    def __isReaderValid(self, readerType):
        return {
            ReaderList["CELRDR"]: True,
            ReaderList["HIDOK"]: True,
        }.get(readerType, False)

    
    def __create_er302_reader(self, port=None):
        self.__close_reader()

        if port is None or port == "" or port == "auto":
            port = find_cp2102()
            if port is None and sys.platform.startswith('win'):
                return self.__fail("ER302 Reader not detected on any port", "NO_READER")
            elif port is None:
                port = ER303_DEFAULT_PORT

        print(f"Attempting to connect ER302 Reader on port: {port}")
        reader = ER302_Reader(port, ER303_DEFAULT_BAUD)
        if not reader.open():
            return self.__fail("ER302 Reader not connected", "NO_READER")

        if not reader.init_reader():
            return self.__fail("ER302 Reader init failed", "NOT_CONNECTED")

        self.er302Reader = reader
        self.hidReader = None
        self.reader_type = ReaderList["CELRDR"]
        return self.__success(reader, "ER302 Reader connected")


    def __create_hid_reader(self):
        self.__close_reader()

        reader = HID_Reader()
        if not reader.open():
            return self.__fail("HID Reader not connected", "NOT_CONNECTED")

        self.hidReader = reader
        self.er302Reader = None
        self.reader_type = ReaderList["HIDOK"]
        return self.__success(reader, "Hid Reader connected")


    def __success(self, reader, message):
        return {
            "status": "success",
            "reader": reader,
            "message": message,
            "readerstatus": "READER_CONNECTED"
        }


    def __is_reader_connected(self):
        if self.reader is None:
            return False
        print("Checking reader connectivity for type:", self.reader_type)

        # Check hardware-level connectivity for ER302
        if self.reader_type == ReaderList["CELRDR"] and hasattr(self.reader, "is_reader_connected"):
            try:
                return self.reader.is_reader_connected()
            except Exception:
                return False

        # For HID, validate if reader object exists; further checks are not available here.
        if self.reader_type == ReaderList["HIDOK"] and hasattr(self.reader, "is_reader_connected"):
            try:
                return self.reader.is_reader_connected()
            except Exception:
                return False

        return False


    def __check_reader(self, response, op_name):
        # When error occurs, validate last reader state and optionally recover.
        print(f"Checking response for {op_name}: {response}")
        if response.get("readerstatus") in ["BAD_REQUEST", "PROCESS_ERROR"]:
            if not self.__is_reader_connected():
                # failed hardware state, report to caller
                self.__close_reader()
                
                return {
                    "status": "fail",
                    "readerstatus": "NO_READER",
                    "message": "No reader connected",
                    "output": None
                }
        return response

    def __fail(self, message, code):
        return {
            "status": "fail",
            "reader": None,
            "message": message,
            "readerstatus": code,
            "output": None
        }


    def __close_reader(self):
        if self.er302Reader is not None:
            try:
                if hasattr(self.er302Reader, "close"):
                    self.er302Reader.close()
            except Exception:
                pass
            self.er302Reader = None

        if self.hidReader is not None:
            try:
                if hasattr(self.hidReader, "close"):
                    self.hidReader.close()
            except Exception:
                pass
            self.hidReader = None

        self.reader = None
        self.reader_type = None


    def __get_reader(self, payload: ReaderRequest):
        reader_type = payload.get("reader")
        reader_port = payload.get("port")

        if not self.__isReaderValid(reader_type):
            return self.__fail("Invalid reader type", "READER_INVALID")

        if reader_type == ReaderList["CELRDR"]:
            if self.er302Reader is not None:
                return self.__success(self.er302Reader, "ER302 Reader connected")
            return self.__create_er302_reader(reader_port)

        if reader_type == ReaderList["HIDOK"]:
            if self.hidReader is not None:
                return self.__success(self.hidReader, "Hid Reader connected")
            return self.__create_hid_reader()

        return self.__fail("Unsupported reader", "READER_INVALID")


    def __current_reader(self, payload):
        try:
            response = self.__get_reader(payload)

            if response.get("status") != "success":
                return {
                    "status": "fail",
                    "readerstatus": response.get("readerstatus"),
                    "message": response.get("message"),
                    "output": None
                }
            self.reader = response["reader"]
            return {
                    "status": "success",
                    "readerstatus": response["readerstatus"],
                    "message": response["message"],
                    "output": None
                }

        except Exception as e:
            print(f"Error in __current_reader: {e}")
            self.er302Reader = None
            self.hidReader = None
            self.reader = None

            return {
                "status": "fail",
                "readerstatus": "NO_READER",
                "message": str(e),
                "output": None
            }

    def init_reader(self, payload: ReaderRequest):
        return self.__current_reader(payload)
    
    def readMemory(self, payload: ReaderRequest):

        if self.reader is None:
            return self.__fail("No reader initialized", "NO_READER")

        try:
            response = self.reader.read_memory(payload)

            return {
                "status": "success" if response["status"] is True else "fail",
                "readerstatus": response["readerstatus"],
                "message": response["message"],
                "output": response["data"] if response.get("status") is True else None
            }

        except Exception as e:
            print(f"Error in readMemory: {e}")
            response = {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e),
                "output": None
            }
            
            return self.__check_reader(response, "readMemory")
                

    
    def writeMemory(self, payload: MemoryUpdateRequest):        
        
        if self.reader is None:
            return self.__fail("No reader initialized", "NO_READER")

        try:
            response = self.reader.write_memory(payload)

            return {
                "status": "success" if response.get("status") else "fail",
                "readerstatus": response.get("readerstatus"),
                "message": response.get("message"),
                "output": response.get("data") if response.get("status") else None
            }

        except Exception as e:
            print(f"Error in writeMemory: {e}")
            response = {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e),
                "output": None
            }
            
            return self.__check_reader(response, "writeMemory")


    def changeSectorKey(self, payload: ReaderRequest):

        if self.reader is None:
            return self.__fail("No reader initialized", "NO_READER")

        try:
            response = self.reader.change_sector_key(payload)

            if response.get("status") is True:
                return {
                    "status": "success",
                    "readerstatus": response.get("readerstatus", "KEY_CHANGED"),
                    "message": response.get("message", "Key updated"),
                    "output": response.get("data")
                }
            else:
                return {
                    "status": "fail",
                    "readerstatus": response.get("readerstatus", "KEY_CHANGE_FAILED"),
                    "message": response.get("message", "Key update failed"),
                    "output": None
                }

        except Exception as e:
            print(f"Error in ReaderClient.secureBlock: {e}")
            response = {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e),
                "output": None
            }
            
            return self.__check_reader(response, "readMemory")
    
    
    def readUID(self):

        if self.reader is None:
            return self.__fail("No reader initialized", "NO_READER")

        try:
            response = self.reader.read_uid()

            return {
                "status": "success" if response.get("status") else "fail",
                "readerstatus": response.get("readerstatus"),
                "message": response.get("message"),
                "output": response.get("data") if response.get("status") else None
            }

        except Exception as e:
            print(f"Error in readUID: {e}")
            response = {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e),
                "output": None
            }
            
            return self.__check_reader(response, "readMemory")