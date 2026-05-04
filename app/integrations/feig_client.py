from app.sdk.feig.provider import FeigReaderProvider

class FeigClient:
    def __init__(self):
        try:
            print("Initializing FeigClient...")
            self.provider = FeigReaderProvider()
        except Exception as e:
            print(f"Error initializing FeigReaderProvider: {e}")
            self.provider = None
    
    def connect(self):
        print("Attempting to connect to FEIG reader...")
        print(f"Provider initialized: {self.provider is not None}")
        if not self.provider:
            return False
        return self.provider.connect()
    
    def disconnect(self):
        if self.provider:
            self.provider.disconnect()
        
    def is_connected(self):
        if not self.provider:
            return False
        return self.provider.is_connected
    
    def inventory(self):
        if not self.provider or not self.provider.is_connected:
            raise ConnectionError("Reader not connected")
            
        return self.provider.inventory()

    def read_tag(self, request):
        if not self.provider or not self.provider.is_connected:
            raise ConnectionError("Reader not connected")
        tags = self.provider.inventory()  # Ensure we have the latest tag info
        if not tags:
            raise ValueError("No tags found during inventory")
        tagId = request.get('tagId', None)
        if tagId is None:
            raise ValueError("tagId is required")
        
        tagIndx = -1
        for idx, tag in enumerate(tags):
            print(f"Checking tag {idx}: {tag} ")
            if tag.id == tagId:
                tagIndx = idx
                break

        if tagIndx < 0 or tagIndx >= len(tags):
            raise ValueError(f"Invalid tagId: {tagId}. Must be between 0 and {len(tags)-1}")
        
        print(f"tags: {tagIndx}")
        startBlock = request.get('startBlock', 0)
        noOfBlocks = request.get('noOfBlocks', 4)
        return self.provider.read_tag(tag_idx=tagIndx, startBlock=startBlock, noOfBlocks=noOfBlocks)

    def write_tag(self, request):
        if not self.provider or not self.provider.is_connected:
            raise ConnectionError("Reader not connected")

        tagId = request.get('tagId', None)
        data = request.get('data', None)
        if tagId is None:
            raise ValueError("tagId is required")

        tags = self.provider.inventory()
        if not tags:
            raise ValueError("No tags found during inventory")

        tagIndx = -1
        for idx, tag in enumerate(tags):
            if tag.id == tagId:
                tagIndx = idx
                break

        if tagIndx < 0 or tagIndx >= len(tags):
            raise ValueError(f"Invalid tagId: {tagId}. Must be between 0 and {len(tags)-1}")

        startBlock = request.get('startBlock', 0)

        return self.provider.write_tag(tag_idx=tagIndx, startBlock=startBlock, data=data)
