from pydantic import BaseModel
from typing import Optional

class MemoryRequest(BaseModel):
    tagId: str
    offset: int = 0
    noOfBlocks: int = 4

class WriteMemoryRequest(BaseModel):
    tagId: str
    offset: int = 0
    data: str

class ConnectRequest(BaseModel):
    connection_str: Optional[str] = "RDType=M201;CommType=USB;AddrMode=0"

class EasRequest(BaseModel):
    tagId: str
    enable: bool

class AfiRequest(BaseModel):
    tagId: str
    afi: int

class ReadCardRequest(BaseModel):
    uid: str
    block: int = 0
    length: int = 16
    key: str = "FFFFFFFFFFFF"

class WriteCardRequest(BaseModel):
    uid: str
    block: int = 0
    data: str
    key: str = "FFFFFFFFFFFF"

class ChangeSectorKeyRequest(BaseModel):
    uid: str
    sector: int
    current_key: str
    new_key: str
    keyB: Optional[str] = None
