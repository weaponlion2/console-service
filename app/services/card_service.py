import time

class CardService:

    def __init__(self, reader_client):
        self.reader_client = reader_client

    def init_reader(self, request):
        result = self.reader_client.init_reader(request.dict())

        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"]
        }

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
        print(f"Read memory result: {result}")

        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"],
            "output": result["output"]
        }


    def read_uid(self):
        result = self.reader_client.readUID()

        return {
            "status": result["status"],
            "readerstatus": result["readerstatus"],
            "message": result["message"],
            "output": result["output"]
        }
        
    def change_sector_key(self, request):
        result = self.reader_client.changeSectorKey(request.dict())

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