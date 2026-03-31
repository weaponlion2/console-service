from fastapi import APIRouter
from app.schemas.sip import SIPItemRequest, SIPPatronRequest, SIPCheckinRequest, SIPCheckoutRequest
from app.schemas.reader import UIDRequest, MemoryRequest, SecureBlockRequest
from app.services.card_service import CardService
from app.integrations.reader_client import ReaderClient

router = APIRouter()
service = CardService(ReaderClient())
reader = ReaderClient()

@router.post("/Patron")
def sip_patron(request: SIPPatronRequest):
    return service.get_patron(request)

@router.post("/Item")
def sip_item(request: SIPItemRequest):
    return service.get_item(request)

@router.post("/Checkout")
def checkout(request: SIPCheckoutRequest):
    return service.checkout(request)

@router.post("/Checkin")
def checkin(request: SIPCheckinRequest):
    return service.checkin(request)

# New RFID routes
@router.get("/uid")
def get_uid(request: UIDRequest):
    return reader.readUID(request.dict())

@router.get("/memory")
def get_memory(request: MemoryRequest):
    return reader.readMemory(request.dict())

@router.post("/memory")
def post_memory(request: MemoryRequest):
    return reader.writeMemory(request.dict())

@router.post("/secure")
def post_secure(request: SecureBlockRequest):
    return reader.secureBlock(request.dict())
