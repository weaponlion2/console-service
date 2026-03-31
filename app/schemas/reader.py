from pydantic import BaseModel

from typing import Dict, Optional, Union

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

class UIDRequest(BaseModel):
    reader: str
    key: str = "FFFFFFFFFFFF"

class MemoryRequest(BaseModel):
    reader: str
    block: int = 1
    length: int = 32
    key: str = "FFFFFFFFFFFF"
    write: Optional[Dict[int, Union[str, list]]] = None

class SecureBlockRequest(BaseModel):
    reader: str
    sector: int = 0
    current_key: str = "FFFFFFFFFFFF"
    new_key: str
    keyB: Optional[str] = None

class PatronResponse(BaseModel):
    status: str
    readerstatus: str
    message: str
    output: str
