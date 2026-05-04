from pydantic import BaseModel


class MemoryRequest(BaseModel):
    tagId: str
    offset: int = 0
    noOfBlocks: int = 4


class WriteMemoryRequest(BaseModel):
    tagId: str
    offset: int = 0
    data: str