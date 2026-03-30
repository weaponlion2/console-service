class ItemService:

    def __init__(self, reader_client):
        self.reader_client = reader_client

    def process_item(self, request):
        result = self.reader_client.execute(request.dict())

        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"],
            "output": result["output"],
            "easstatus": result.get("easstatus", ""),
            "afi": result.get("afi", "")
        }
