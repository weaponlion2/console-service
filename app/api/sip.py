from fastapi import APIRouter
from app.schemas.sip import SIPItemRequest, SIPPatronRequest, SIPCheckinRequest, SIPCheckoutRequest
from app.services.patron_service import PatronService
from app.integrations.reader_client import ReaderClient

router = APIRouter()
service = PatronService(ReaderClient())

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
