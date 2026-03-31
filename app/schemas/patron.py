from pydantic import BaseModel

class MemoryRequest(BaseModel):
    reader: str
    port: int = 0
    cardtype: str = "MIFARE"
    key: str = "FFFFFFFFFFFF"
    startblock: int = 1
    startindex: int = 0
    length: int = 32
    sessionid: str = ""
    

class UIDRequest(BaseModel):
    reader: str
    port: int = 0
    

class PatronRequest(BaseModel):
    reader: str
    port: int = 0
    cardtype: str = "MIFARE"
    key: str = "FFFFFFFFFFFF"
    startblock: int = 1
    startindex: int = 0
    length: int = 32
    sessionid: str = ""

class PatronResponse(BaseModel):
    status: str
    readerstatus: str
    message: str
    output: str
