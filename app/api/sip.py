from fastapi import APIRouter
from app.schemas.sip import (
    SIPItemRequest, SIPPatronRequest, SIPCheckinRequest, SIPCheckoutRequest,
    SIPRenewRequest, SIPReserveRequest, SIPFineRequest
)
from app.schemas.reader import UIDRequest, MemoryRequest, SecureBlockRequest
from app.services.sip_service import SIPService
from app.integrations.sip_client import SIPClient
from app.integrations.reader_client import ReaderClient

router = APIRouter()
sip_service = SIPService(SIPClient())
reader = ReaderClient()

@router.post("/patron")
def sip_patron(request: SIPPatronRequest):
    """Get patron information"""
    return sip_service.get_patron(request)

@router.post("/item")
def sip_item(request: SIPItemRequest):
    """Get item information"""
    return sip_service.get_item(request)

@router.post("/checkout")
def checkout(request: SIPCheckoutRequest):
    """Checkout item for patron"""
    return sip_service.checkout(request)

@router.post("/checkin")
def checkin(request: SIPCheckinRequest):
    """Checkin item"""
    return sip_service.checkin(request)

@router.post("/renew")
def renew(request: SIPRenewRequest):
    """Renew item for patron"""
    return sip_service.renew(request)

@router.post("/reserve")
def reserve(request: SIPReserveRequest):
    """Reserve item for patron"""
    return sip_service.reserve(request)

@router.post("/pay-fine")
def pay_fine(request: SIPFineRequest):
    """Pay fine for patron"""
    return sip_service.pay_fine(request)

