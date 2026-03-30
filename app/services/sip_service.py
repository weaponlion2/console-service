class SIPService:

    def __init__(self, sip_client):
        self.sip_client = sip_client

    def get_patron(self, request):
        return self.sip_client.patron(request.dict())

    def get_item(self, request):
        return self.sip_client.item(request.dict())

    def checkout(self, request):
        return self.sip_client.checkout(request.dict())

    def checkin(self, request):
        return self.sip_client.checkin(request.dict())
