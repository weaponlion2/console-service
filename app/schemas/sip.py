from pydantic import BaseModel
from typing import List, Dict, Any

class SIPInfo(BaseModel):
    host: str
    port: str
    user: str
    password: str
    loccd: str = ""
    libid: str = ""

# Patron
class SIPPatronRequest(BaseModel):
    patronid: str
    pin: str
    sipinfo: SIPInfo

class SIPPatronResponse(BaseModel):
    issueditems: List[Dict[str, Any]]
    message: str
    patron: Dict[str, Any]
    status: str

# Item
class SIPItemRequest(BaseModel):
    itemid: str
    sipinfo: SIPInfo

class SIPItemResponse(BaseModel):
    itemid: str
    itemstatus: str
    statuscd: str
    message: str
    status: str
    title: str

# Checkout / Checkin
class SIPCheckoutRequest(BaseModel):
    patronid: str
    pin: str
    itemid: str
    sipinfo: SIPInfo

class SIPCheckinRequest(BaseModel):
    itemid: str
    sipinfo: SIPInfo
