from pydantic import BaseModel
from typing import Dict, Optional, Union

class MemoryRequest(BaseModel):
    reader: str
    port: int = 0
    cardtype: str = "MIFARE"
    key: str = "FFFFFFFFFFFF"
    block: int = 0
    length: int = 32
    sessionid: str = ""
    
class MemoryUpdateRequest(BaseModel):
    reader: str
    port: int = 0
    cardtype: str = "MIFARE"
    key: str = "FFFFFFFFFFFF"
    block: int = 0
    sessionid: str = ""
    value: str = ""

class UIDRequest(BaseModel):
    reader: str
    port: int = 0
    

class PatronRequest(BaseModel):
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

class SecureBlockRequest(BaseModel):
    reader: str
    block: int
    current_key: str
    new_key: str
    keyB: Optional[str] = None