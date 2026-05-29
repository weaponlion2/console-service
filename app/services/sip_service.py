from app.integrations.sip_client import SIPClient
from app.schemas.sip import (
    SIPPatronRequest, SIPItemRequest, SIPCheckoutRequest, 
    SIPCheckinRequest, SIPRenewRequest, SIPReserveRequest, SIPFineRequest
)

class SIPService:
    """
    Service layer for SIP operations
    Handles business logic and request/response formatting
    """

    def __init__(self, sip_client: SIPClient = None):
        self.sip_client = sip_client or SIPClient()

    def get_patron(self, request: SIPPatronRequest):
        """
        Get patron information
        Workflow: Initialize -> Send request to client -> Return formatted response
        """
        try:
            self.sip_client.initialize(request.sipinfo)
            response = self.sip_client.get_patron(request.patronid, request.pin)
            return response
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e),
                "patron": None,
                "issueditems": []
            }

    def get_item(self, request: SIPItemRequest):
        """
        Get item information
        Workflow: Initialize -> Send request to client -> Return formatted response
        """
        try:
            self.sip_client.initialize(request.sipinfo)
            response = self.sip_client.get_item(request.itemid)
            return response
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e),
                "itemid": request.itemid,
                "title": None,
                "statuscd": None,
                "itemstatus": None
            }

    def checkout(self, request: SIPCheckoutRequest):
        """
        Checkout item for patron
        Workflow: Initialize -> Send request to client -> Return formatted response
        """
        try:
            self.sip_client.initialize(request.sipinfo)
            response = self.sip_client.checkout(request.patronid, request.itemid, request.pin)
            return response
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e),
                "txnstatus": None,
                "patron": None,
                "item": None
            }

    def checkin(self, request: SIPCheckinRequest):
        """
        Checkin item
        Workflow: Initialize -> Send request to client -> Return formatted response
        """
        try:
            self.sip_client.initialize(request.sipinfo)
            response = self.sip_client.checkin(request.itemid)
            return response
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e),
                "txnstatus": None,
                "item": None,
                "patron": None,
                "hold": None
            }

    def renew(self, request: SIPRenewRequest):
        """
        Renew item for patron
        Workflow: Initialize -> Send request to client -> Return formatted response
        """
        try:
            self.sip_client.initialize(request.sipinfo)
            response = self.sip_client.renew(request.patronid, request.itemid, request.pin)
            return response
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e),
                "txnstatus": None,
                "patron": None,
                "item": None
            }

    def reserve(self, request: SIPReserveRequest):
        """
        Reserve item for patron
        Workflow: Initialize -> Send request to client -> Return formatted response
        """
        try:
            self.sip_client.initialize(request.sipinfo)
            response = self.sip_client.reserve(request.patronid, request.itemid, request.pin)
            return response
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e),
                "txnstatus": None,
                "patron": None,
                "item": None
            }

    def pay_fine(self, request: SIPFineRequest):
        """
        Pay fine for patron
        Workflow: Initialize -> Send request to client -> Return formatted response
        """
        try:
            self.sip_client.initialize(request.sipinfo)
            response = self.sip_client.pay_fine(
                request.patronid,
                request.amount,
                request.finetype,
                request.paymentmode,
                request.txnid
            )
            return response
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e)
            }
