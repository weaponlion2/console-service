from fastapi import APIRouter
from app.schemas.patron import PatronRequest, MemoryRequest, UIDRequest
from app.services.patron_service import PatronService
from app.integrations.reader_client import ReaderClient
from app.services.system_service import generate_serial_key

router = APIRouter()
service = PatronService(ReaderClient())

@router.post("/Patron")
def patron(request: PatronRequest):
    print(request)
    return service.process_patron(request)

@router.get("/memory")
def memory(request: MemoryRequest):
    print(request)
    return service.process_memory(request)

@router.get("/uid")
def uid(request: UIDRequest):
    print(request)
    return service.process_uid(request)

@router.post("/read_card")
def patron(request: PatronRequest):
    return service.process_read_card(request)


@router.get("/Patron")
def patron():
    return "Hello"

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