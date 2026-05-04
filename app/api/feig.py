from fastapi import APIRouter
from app.schemas.feig import WriteMemoryRequest, MemoryRequest
from app.services.feig_service import FeigService
from app.integrations.feig_client import FeigClient

router = APIRouter()
# Dedicated service and client for FEIG
service = FeigService(FeigClient())

@router.post("/connect")
def connect():
    """Initialize and connect to the FEIG reader."""
    return service.connect_reader()

@router.get("/inventory")
def inventory():
    """Perform an inventory scan (read UID) on the FEIG reader."""
    return service.get_inventory()

@router.post("/read")
def read(request: MemoryRequest):
    """Read memory from a tag using FEIG reader."""
    return service.read_memory(request)

@router.post("/write")
def write(request: WriteMemoryRequest):
    """Write memory to a tag using FEIG reader."""
    return service.write_memory(request)
