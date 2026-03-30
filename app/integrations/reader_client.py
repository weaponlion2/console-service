from app.schemas.patron import PatronRequest as ReaderRequest
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

    
    def __changeReaderBasedOnRequest(self, payload: ReaderRequest):
        readerType = payload["reader"]
        
        if(self.__isReaderValid(readerType) == False) : return {
            "status": False,
            "readerValue": None,
            "message": "Invalid reader type",
            "readerstatus": "READER_INVALID"
        }
                
        if(readerType == ReaderList["CELRDR"]):
            if self.er302Reader is None:                
                Reader = ER302_Reader(ER303_DEFAULT_PORT, ER303_DEFAULT_BAUD)
                self.hidReader = None
                if Reader.open():
                    if Reader.init_reader():
                        self.er302Reader = Reader
                        return {
                            "status": True,
                            "readerValue": Reader,
                            "message": "ER302 Reader connected",
                            "readerstatus": "READER_CONNECTED"
                        }
                    else: return {
                    "status": False,
                    "readerValue": None,
                    "message": "ER302 Reader not connected",
                    "readerstatus": "NOT_CONNECTED"
                }
                return {
                    "status": False,
                    "readerValue": None,
                    "message": "ER302 Reader not connected",
                    "readerstatus": "NO_READER"
                }
            else: return {
            "status": True,
            "readerValue": self.er302Reader,
            "message": "ER302 Reader connected",
            "readerstatus": "READER_CONNECTED"
        }
                
        if(readerType == ReaderList["HIDOK"]):
            if self.hidReader is None:
                Reader = HID_Reader() 
                self.er302Reader = None
                if Reader.open():
                    self.hidReader = Reader
                    return {
                                "status": True,
                                "readerValue": Reader,
                                "message": "Hid Reader connected",
                                "readerstatus": "READER_CONNECTED"
                            }
                else: return {
                        "status": False,
                        "readerValue": None,
                        "message": "Hid Reader not connected",
                        "readerstatus": "NOT_CONNECTED"
                    }
            else: return {
            "status": True,
            "readerValue": self.hidReader,
            "message": "Hid Reader connected",
            "readerstatus": "READER_CONNECTED"
            }
        
        return None
        
        

    def execute(self, payload: ReaderRequest):
        # Replace with actual hardware SDK
        return {
            "status": "success",
            "readerstatus": "CARD_VALID",
            "message": "Mock response",
            # "output": payload.get("input", "LS01"),
            "output": "LS01"
        }

    def findPatron(self, payload: ReaderRequest):
        try:
            readerResponse = self.__changeReaderBasedOnRequest(payload)
            if readerResponse["status"] is False:
                return {
                    "status": "fail",
                    "readerstatus": readerResponse["readerstatus"],
                    "message": readerResponse["message"],
                    "output": None
                }
            currentReaderInstance = readerResponse["readerValue"]
            if currentReaderInstance is not None:
                (isUid, isMem, isWrite, isSecure) = self.__typeOfRequestCommand(payload["command"])
                if isUid is True or isMem is True:                
                    cardResponse = (currentReaderInstance.read_card(isMem))
                    if cardResponse["status"] is True:
                        return {
                            "status": "success",
                            "readerstatus": cardResponse["readerstatus"],
                            "message": cardResponse["message"],
                            "output": cardResponse["data"]
                        }
                    else: return {
                        "status": "fail",
                        "readerstatus": cardResponse["readerstatus"],
                        "message": cardResponse["message"],
                        "output": None
                    }
            else:
                return {
                    "status": "fail",
                    "readerstatus": "NO_READER",
                    "message": "No reader is attached to PC",
                    "output": None
                }
        except Exception as e:
            self.er302Reader = None
            self.hidReader = None
            return {
                    "status": "fail",
                    "readerstatus": "NO_READER",
                    "message": e,
                    "output": None
                }
    
    
    def readCard(self, payload: ReaderRequest):
        try:
            readerResponse = self.__changeReaderBasedOnRequest(payload)
            if readerResponse["status"] is False:
                return {
                    "status": "fail",
                    "readerstatus": readerResponse["readerstatus"],
                    "message": readerResponse["message"],
                    "output": None
                }
            currentReaderInstance = readerResponse["readerValue"]
            if currentReaderInstance is not None:
                (isUid, isMem, isWrite, isSecure) = self.__typeOfRequestCommand(payload["command"])
                if isUid is True or isMem is True:
                    
                    cardResponse = (currentReaderInstance.read_cardV2(payload))
                    if cardResponse["status"] is True:
                        return {
                            "status": "success",
                            "readerstatus": cardResponse["readerstatus"],
                            "message": cardResponse["message"],
                            "output": cardResponse["data"]
                        }
                    else: return {
                        "status": "fail",
                        "readerstatus": cardResponse["readerstatus"],
                        "message": cardResponse["message"],
                        "output": None
                    }
            else:
                return {
                    "status": "fail",
                    "readerstatus": "NO_READER",
                    "message": "No reader is attached to PC",
                    "output": None
                }
        except Exception as e:
            print(f"Error in ReaderClient.readCard: {e}")  
            self.er302Reader = None
            self.hidReader = None
            return {
                    "status": "fail",
                    "readerstatus": "NO_READER",
                    "message": e,
                    "output": None
                }
    
    
    def __typeOfRequestCommand(self, command):
        command_map = {
            "GETUID": (True, False, False, False),
            "GETMEMID": (False, True, False, False),
            "SETMEMID": (False, False, True, False ),
            "SECUREBLK": (False, False, False, True),
            
        }
        if command not in command_map:
            raise (False, False, False, False)
        return command_map[command]