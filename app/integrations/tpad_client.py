from app.sdk.tpad.rfid_service import RFIDService
import threading

class TpadClient:
    def __init__(self):
        try:
            print("Initializing TpadClient...")
            self.service = RFIDService()
            self._is_connected = False
            self.lock = threading.Lock()
        except Exception as e:
            print(f"Error initializing RFIDService: {e}")
            self.service = None
            self._is_connected = False
    
    def connect(self, connection_str="RDType=RL8000;CommType=USB;AddrMode=0"):
        print(f"Attempting to connect to TPAD reader with {connection_str}...")
        if not self.service:
            return False
        
        with self.lock:
            self._is_connected = self.service.connect(connection_str)
            return self._is_connected
    
    def disconnect(self):
        if self.service:
            with self.lock:
                self.service.disconnect()
                self._is_connected = False
        
    def is_connected(self):
        return self._is_connected
    
    def inventory(self):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")
            
        return self.service.get_inventory()

    def read_tag(self, request):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")
        
        tagId = request.get('tagId', None)
        if tagId is None:
            raise ValueError("tagId is required")
        
        # Optionally verify if tag is in inventory like FeigClient does
        tags = self.service.get_inventory()
        if not tags:
            raise ValueError("No tags found during inventory")
        
        tag_found = False
        # Assuming tags are either strings (UIDs) or objects with an 'id' attribute
        for tag in tags:
            current_id = tag.uid if hasattr(tag, 'uid') else tag
            if current_id == tagId:
                tag_found = True
                break
        
        if not tag_found:
             raise ValueError(f"Tag with ID {tagId} not found in inventory")

        offset = request.get('offset', 0)
        noOfBlocks = request.get('noOfBlocks', 4)
        
        # read_tag_blocks returns a list of data blocks
        results = self.service.read_tag_blocks(uid=tagId, start_block=offset, count=noOfBlocks)
        
        if results is None:
            return None
            
        # FeigClient return format is likely a hex string or similar. 
        # RFIDService.read_tag_blocks returns a list of results (likely bytes or hex).
        # Let's join them if they are hex strings or convert them.
        # Looking at rfid_service.py, iso15693_read_block returns 'data'.
        
        # If the expected output is a single hex string:
        hex_data = ""
        for block in results:
            if block:
                if isinstance(block, bytes):
                    hex_data += block.hex().upper()
                elif isinstance(block, list):
                    hex_data += "".join(f"{b:02X}" for b in block)
                else:
                    hex_data += str(block)
        
        return hex_data

    def write_tag(self, request):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")

        tagId = request.get('tagId', None)
        data = request.get('data', None)
        if tagId is None:
            raise ValueError("tagId is required")
        if data is None:
            raise ValueError("data is required")

        # data should be a list of 4 bytes per block or similar depending on the SDK
        # If data is a hex string, we might need to convert it.
        if isinstance(data, str):
            # Convert hex string to list of integers
            data_bytes = [int(data[i:i+2], 16) for i in range(0, len(data), 2)]
        else:
            data_bytes = data

        offset = request.get('offset', 0)
        
        # RFIDService.write_tag_block writes a single block. 
        # If data is more than one block, we might need to write multiple times.
        if len(data_bytes) > 4:
            success = True
            for i in range(0, len(data_bytes), 4):
                block_num = offset + (i // 4)
                chunk = data_bytes[i:i+4]
                if not self.service.write_tag_block(uid=tagId, block_num=block_num, data=chunk):
                    success = False
                    break
            return success
        else:
            return self.service.write_tag_block(uid=tagId, block_num=offset, data=data_bytes)

    def check_eas(self, tagId):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")
        
        # Try NXP iCode SLI first
        status = self.service.check_eas(tagId)
        if status is None:
            # Try EM4237
            status = self.service.check_em4237_eas(tagId)
        
        return status

    def set_eas(self, tagId, enable: bool):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")
        
        if enable:
            return self.service.enable_eas(tagId) or self.service.enable_em4237_eas(tagId)
        else:
            return self.service.disable_eas(tagId) or self.service.disable_em4237_eas(tagId)

    def set_afi(self, tagId, afi: int):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")
        
        return self.service.write_afi(tagId, afi)

    def get_afi(self, tagId):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")
        
        info = self.service.get_tag_system_info(tagId)
        if info:
            return info.get("afi")
        return None

    def get_card_info(self, uid):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")
        
        return self.service.get_card_info(uid)

    def read_card(self, uid, block, length, key="FFFFFFFFFFFF"):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")
        
        return self.service.read_card(uid, block, length, key)

    def write_card(self, uid, block, data, key="FFFFFFFFFFFF"):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")
        
        return self.service.write_card(uid, block, data, key)

    def change_sector_key(self, uid, sector, current_key, new_key, keyB=None):
        if not self.service or not self._is_connected:
            raise ConnectionError("Reader not connected")
        
        return self.service.changesectorkey(uid, sector, current_key, new_key, keyB)
