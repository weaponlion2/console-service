from app.integrations.feig_client import FeigClient
class FeigService:
    def __init__(self, client: FeigClient):
        self.client = client

    def connect_reader(self):
        success = self.client.connect()
        if success:
            return {
                "status": "success",
                "readerstatus": "READER_CONNECTED",
                "message": "FEIG Reader connected successfully"
            }
        else:
            return {
                "status": "fail",
                "readerstatus": "NOT_CONNECTED",
                "message": "Failed to connect to FEIG Reader"
            }

    def get_inventory(self):
        try:
            tags = self.client.inventory()
            if tags:
                print(f"Inventory found {(tags)} tags")
                # Map the first tag's ID to a response
                # tags = [<TagInfo id='E00401086E01FEB1' rssi=0dBm>, <TagInfo id='E00401083BC626F4' rssi=0dBm>]
                # uid = str(tags[0].id) if hasattr(tags[0], 'id') else None
                return {
                    "status": "success",
                    "readerstatus": "INVENTORY_SUCCESS",
                    "message": "Inventory scan successful",
                    "output": [tag.id for tag in tags if hasattr(tag, 'id')]
                }
            return {
                "status": "fail",
                "readerstatus": "NO_TAGS_FOUND",
                "message": "No tags detected during inventory scan",
                "output": None
            }
        except Exception as e:
            return {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e),
                "output": None
            }

    def read_memory(self, request):
        try:
            print(f"Read request received: {request}")

            data = self.client.read_tag(request.dict())
            print(f"Data read from tag: {data}")
            if data:
                return {
                    "status": "success",
                    "readerstatus": "READ_SUCCESS",
                    "message": "Data read successfully",
                    "output": data
                }
            return {
                "status": "fail",
                "readerstatus": "READ_FAILED",
                "message": "Failed to read data from tag",
                "output": None
            }
        except Exception as e:
            return {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e),
                "output": None
            }

    def write_memory(self, request):
        try:
            success = self.client.write_tag(request.dict())
            if success:
                return {
                    "status": "success",
                    "readerstatus": "WRITE_SUCCESS",
                    "message": "Data written successfully"
                }
            return {
                "status": "fail",
                "readerstatus": "WRITE_FAILED",
                "message": "Failed to write data to tag"
            }
        except Exception as e:
            return {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e)
            }
