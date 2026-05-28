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
