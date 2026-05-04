from pydantic import BaseModel


class MemoryRequest(BaseModel):
    tagId: str
    startBlock: int = 0
    noOfBlocks: int = 4


class WriteMemoryRequest(BaseModel):
    tagId: str
    startBlock: int = 0
    data: str