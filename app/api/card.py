from fastapi import APIRouter
from app.schemas.card import ReaderRequest, MemoryRequest, SecureSectorRequest, MemoryUpdateRequest
from app.services.card_service import CardService
from app.integrations.reader_client import ReaderClient
from app.services.system_service import generate_serial_key

router = APIRouter()
service = CardService(ReaderClient())


@router.post("/reader")
def memory(request: ReaderRequest):
    return service.init_reader(request)

@router.post("/memory")
def memory(request: MemoryRequest):
    return service.read_memory(request)

@router.put("/memory")
def memory(request: MemoryUpdateRequest):
    return service.write_memory(request)

@router.get("/uid")
def uid():
    return service.read_uid()

@router.post("/sectorkey")
def sector_key(request: SecureSectorRequest):
    return service.change_sector_key(request)


@router.get("/")
def health():
    return "Service is running"

@router.post("/login")
def login():
    return {
        "sessionid": 
            "5pPS0Tc5kUOTr1HPARhHoSh18pSqXMJWB1/3/pFL1TlPqAl74DzJS2RF2/fDJttTpM1dcz/d0+oNbWx+TYNSdQ==",
            "status": "success",
            "updaterequired": False
            }
    

@router.get("/serialkey")
def serial_key():
    return {
        "serialkey": generate_serial_key(),
        "status": "success"
        }