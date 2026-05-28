from app.integrations.tpad_client import TpadClient

class TpadService:
    def __init__(self, client: TpadClient):
        self.client = client
        self.is_connected = False

    def connect_reader(self, connection_str=None):
        if self.is_connected:
            return {
                "status": "success",
                "readerstatus": "READER_ALREADY_CONNECTED",
                "message": "TPAD Reader is already connected"
            }

        if connection_str:
            success = self.client.connect(connection_str)
        else:
            success = self.client.connect()
            
        if success:
            self.is_connected = True
            return {
                "status": "success",
                "readerstatus": "READER_CONNECTED",
                "message": "TPAD Reader connected successfully"
            }
        else:
            return {
                "status": "fail",
                "readerstatus": "NOT_CONNECTED",
                "message": "Failed to connect to TPAD Reader"
            }

    def get_inventory(self):
        try:
            tags = self.client.inventory()
            if tags:
                print(f"Inventory found {len(tags)} tags")
                for tag in tags:
                    print("Tag UID: ", getattr(tag, 'uid', 'N/A'))
                return {
                    "status": "success",
                    "readerstatus": "INVENTORY_SUCCESS",
                    "message": "Inventory scan successful",
                    "output": [tag.uid if hasattr(tag, 'uid') else str(tag) for tag in tags]
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
            data = self.client.read_tag(request.dict())
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

    def check_eas_status(self, tagId: str):
        try:
            status = self.client.check_eas(tagId)
            if status is not None:
                return {
                    "status": "success",
                    "readerstatus": "EAS_CHECK_SUCCESS",
                    "message": f"EAS Status: {'ACTIVE' if status else 'INACTIVE'}",
                    "output": {"eas_active": status}
                }
            return {
                "status": "fail",
                "readerstatus": "EAS_CHECK_FAILED",
                "message": "Failed to check EAS status"
            }
        except Exception as e:
            return {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e)
            }

    def set_eas_status(self, request):
        try:
            success = self.client.set_eas(request.tagId, request.enable)
            if success:
                return {
                    "status": "success",
                    "readerstatus": "EAS_SET_SUCCESS",
                    "message": f"EAS {'ENABLED' if request.enable else 'DISABLED'} successfully"
                }
            return {
                "status": "fail",
                "readerstatus": "EAS_SET_FAILED",
                "message": f"Failed to {'enable' if request.enable else 'disable'} EAS"
            }
        except Exception as e:
            return {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e)
            }

    def write_afi_value(self, request):
        try:
            success = self.client.set_afi(request.tagId, request.afi)
            if success:
                return {
                    "status": "success",
                    "readerstatus": "AFI_WRITE_SUCCESS",
                    "message": f"AFI set to {hex(request.afi)} successfully"
                }
            return {
                "status": "fail",
                "readerstatus": "AFI_WRITE_FAILED",
                "message": "Failed to write AFI"
            }
        except Exception as e:
            return {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e)
            }

    def check_afi_value(self, tagId: str):
        try:
            afi = self.client.get_afi(tagId)
            if afi is not None:
                return {
                    "status": "success",
                    "readerstatus": "AFI_CHECK_SUCCESS",
                    "message": f"Current AFI: {hex(afi)}",
                    "output": {"afi": afi, "afi_hex": hex(afi)}
                }
            return {
                "status": "fail",
                "readerstatus": "AFI_CHECK_FAILED",
                "message": "Failed to check AFI value"
            }
        except Exception as e:
            return {
                "status": "fail",
                "readerstatus": "PROCESS_ERROR",
                "message": str(e)
            }
