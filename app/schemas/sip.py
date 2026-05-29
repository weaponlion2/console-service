from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SIPInfo(BaseModel):
    host: str
    port: int
    user: str
    password: str
    loccd: str = ""
    libid: str = ""

# ============= Data Models =============
class Patron(BaseModel):
    patronid: str
    name: Optional[str] = None
    fine: Optional[float] = 0.0
    isvalid: Optional[str] = "NA"
    isvalidpwd: Optional[str] = "NA"
    email: Optional[str] = None
    contactno: Optional[str] = None
    issueditems: Optional[int] = 0
    holditems: Optional[int] = 0
    overdueitems: Optional[int] = 0

class Item(BaseModel):
    itemid: str
    title: Optional[str] = None
    duedate: Optional[str] = None

class HoldDetails(BaseModel):
    patronid: str
    libraryid: Optional[str] = None
    details: Optional[str] = None

# ============= Request Models =============
class SIPPatronRequest(BaseModel):
    patronid: str
    pin: Optional[str] = None
    sipinfo: SIPInfo

class SIPItemRequest(BaseModel):
    itemid: str
    sipinfo: SIPInfo

class SIPCheckoutRequest(BaseModel):
    patronid: str
    pin: Optional[str] = None
    itemid: str
    sipinfo: SIPInfo

class SIPCheckinRequest(BaseModel):
    itemid: str
    sipinfo: SIPInfo

class SIPRenewRequest(BaseModel):
    patronid: str
    pin: Optional[str] = None
    itemid: str
    sipinfo: SIPInfo

class SIPReserveRequest(BaseModel):
    patronid: str
    pin: Optional[str] = None
    itemid: str
    sipinfo: SIPInfo

class SIPFineRequest(BaseModel):
    patronid: str
    amount: float
    finetype: str = "01"
    paymentmode: str = "00"
    txnid: str = ""
    sipinfo: SIPInfo

# ============= Response Models =============
class SIPPatronResponse(BaseModel):
    status: str
    message: Optional[str] = None
    patron: Optional[Patron] = None
    issueditems: Optional[List[Item]] = []

class SIPItemResponse(BaseModel):
    status: str
    itemid: str
    title: Optional[str] = None
    statuscd: Optional[str] = None
    itemstatus: Optional[str] = None
    message: Optional[str] = None

class SIPCheckoutResponse(BaseModel):
    status: str
    txnstatus: Optional[str] = None
    patron: Optional[Patron] = None
    item: Optional[Item] = None
    message: Optional[str] = None

class SIPCheckinResponse(BaseModel):
    status: str
    txnstatus: Optional[str] = None
    item: Optional[Item] = None
    patron: Optional[Patron] = None
    hold: Optional[HoldDetails] = None
    message: Optional[str] = None

class SIPRenewResponse(BaseModel):
    status: str
    txnstatus: Optional[str] = None
    patron: Optional[Patron] = None
    item: Optional[Item] = None
    message: Optional[str] = None

class SIPReserveResponse(BaseModel):
    status: str
    txnstatus: Optional[str] = None
    patron: Optional[Patron] = None
    item: Optional[Item] = None
    message: Optional[str] = None

class SIPFineResponse(BaseModel):
    status: str
    message: Optional[str] = None
