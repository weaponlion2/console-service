import time

class CardService:

    def __init__(self, reader_client):
        self.reader_client = reader_client


    def process_read_card(self, request):
        result = self.reader_client.readMemory(request.dict())

        time.sleep(0.5)
        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"],
            "output": result["output"]
        }
    
    def read_memory(self, request):
        result = self.reader_client.readMemory(request.dict())

        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"],
            "output": result["output"]
        }


    def read_uid(self, request):
        result = self.reader_client.readUID(request.dict())

        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"],
            "output": result["output"]
        }
        
    def change_block_key(self, request):
        result = self.reader_client.changeBlockKey(request.dict())

        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"],
            "output": result["output"]
        }

    def write_memory(self, request):
        result = self.reader_client.writeMemory(request.dict())

        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"],
            "output": result["output"]
        }