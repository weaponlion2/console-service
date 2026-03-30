from pydantic import BaseModel

class ItemRequest(BaseModel):
    reader: str
    port: int = 0
    command: str
    input: str
    secure: str = ""
    afi: str = ""

class ItemResponse(BaseModel):
    status: str
    readerstatus: str
    message: str
    output: str
    easstatus: str
    afi: str
