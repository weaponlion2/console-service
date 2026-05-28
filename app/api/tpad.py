from fastapi import APIRouter, Query
from app.schemas.tpad import WriteMemoryRequest, MemoryRequest, ConnectRequest, EasRequest, AfiRequest
from app.services.tpad_service import TpadService
from app.integrations.tpad_client import TpadClient

router = APIRouter()
# Dedicated service and client for TPAD
service = TpadService(TpadClient())

@router.post("/connect")
def connect(request: ConnectRequest = None):
    """Initialize and connect to the TPAD reader."""
    connection_str = request.connection_str if request else None
    return service.connect_reader(connection_str)

@router.get("/inventory")
def inventory():
    """Perform an inventory scan (read UID) on the TPAD reader."""
    return service.get_inventory()

@router.post("/read")
def read(request: MemoryRequest):
    """Read memory from a tag using TPAD reader."""
    return service.read_memory(request)

@router.post("/write")
def write(request: WriteMemoryRequest):
    """Write memory to a tag using TPAD reader."""
    return service.write_memory(request)

@router.get("/eas")
def check_eas(tagId: str = Query(...)):
    """Check EAS status of a tag."""
    return service.check_eas_status(tagId)

@router.post("/eas")
def set_eas(request: EasRequest):
    """Enable or disable EAS on a tag."""
    return service.set_eas_status(request)

@router.post("/afi")
def write_afi(request: AfiRequest):
    """Write AFI value to a tag."""
    return service.write_afi_value(request)

@router.get("/afi")
def check_afi(tagId: str = Query(...)):
    """Check AFI value of a tag."""
    return service.check_afi_value(tagId)
