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


class SecureSectorRequest(BaseModel):
    sector: int
    current_key: str
    new_key: str
    keyB: Optional[str] = None
    
class HexStringRequest(BaseModel):
    data: str
