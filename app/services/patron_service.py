import time

class PatronService:

    def __init__(self, reader_client):
        self.reader_client = reader_client

    def process_patron(self, request):
        result = self.reader_client.findPatron(request.dict())

        time.sleep(0.5)
        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"],
            "output": result["output"]
        }

    def process_read_card(self, request):
        result = self.reader_client.readCard(request.dict())

        time.sleep(0.5)
        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"],
            "output": result["output"]
        }
