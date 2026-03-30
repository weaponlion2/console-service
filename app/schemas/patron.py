from pydantic import BaseModel

class PatronRequest(BaseModel):
    reader: str
    port: int = 0
    command: str
    input: str
    cardtype: str = "MIFARE"
    key: str = "FFFFFFFFFFFF"
    startblock: int = 1
    startindex: int = 0
    length: int = 32
    secureblock: str = ""
    seckey: str = ""
    sessionid: str = ""
    format: str = ""

class PatronResponse(BaseModel):
    status: str
    readerstatus: str
    message: str
    output: str
