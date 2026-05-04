from pydantic import BaseModel
from typing import Optional

class ReaderRequest(BaseModel):
    reader: str
    port: str = ""

    
class MemoryRequest(BaseModel):
    cardtype: str = "MIFARE"
    key: str = "FFFFFFFFFFFF"
    block: int = 0
    length: int = 32
    
class MemoryUpdateRequest(BaseModel):
    cardtype: str = "MIFARE"
    key: str = "FFFFFFFFFFFF"
    block: int = 0
    sessionid: str = ""
    data: str = ""

class InternalPatronRequest(BaseModel):
    reader: str
    port: int = 0
    cardtype: str = "MIFARE"
    key: str = "FFFFFFFFFFFF"
    block: int = 0
    length: int = 32
    sessionid: str = ""

class PatronResponse(BaseModel):
    status: str
    readerstatus: str
    message: str
    output: str

class SecureSectorRequest(BaseModel):
    sector: int
    current_key: str
    new_key: str
    keyB: Optional[str] = None
    
class HexStringRequest(BaseModel):
    data: str
