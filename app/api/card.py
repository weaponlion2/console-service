import sys
from fastapi import APIRouter, Query
from app.schemas.card import HexStringRequest, ReaderRequest, MemoryRequest, SecureSectorRequest, MemoryUpdateRequest, SerialKeyRequest
from app.services.card_service import CardService
from app.integrations.reader_client import ReaderClient
from app.services.system_service import generate_serial_key, validate_serial_key
from app.utils.detect_port import find_cp2102

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
    try:
        serial_key = generate_serial_key()
        return {
            "status": "success",
            "serial_key": serial_key
        }
    except Exception as e:
        return {
            "status": "fail",
            "message": str(e)
        }
    

@router.post("/serialinfo")
def serial_info(request: SerialKeyRequest):
    try:
        device_info = validate_serial_key(request.serial_key)
        
        if "error" in device_info:
            return {
                "status": "fail",
                "message": device_info["error"]
            }

        return {
            "status": "success",
            "device_info": device_info
        }
    except Exception as e:
        return {
            "status": "fail",
            "message": str(e)
        }
    

@router.post("/str-to-hex")
def str_to_hex(request: HexStringRequest):
    try:
        hex_data = request.data.encode('utf-8').hex().upper()
        return {
            "value": hex_data,
            "status": "success"
        }
    except Exception as e:
        return {
            "status": "fail",
            "message": str(e)
        }

@router.post("/hex-to-str")
def hex_to_str(request: HexStringRequest):
    try:
        data = bytes.fromhex(request.data).decode('utf-8')
        return {
            "value": data,
            "status": "success"
        }
    except Exception as e:
        return {
            "status": "fail",
            "message": f"Invalid hex string: {e}"
        }

@router.get("/detect-port")
def detectPort():
    try:
        detectPlatform = "windows" if sys.platform.startswith('win') else "linux"
        port = find_cp2102()
        if port:
            return {
                "status": "success",
                "port": port,
                "platform": detectPlatform
            }
        else:
            return {
                "status": "fail",
                "message": "CP2102 device not found",
                "platform": detectPlatform
            }
    except Exception as e:
        print(f"Error in detectPort: {e}")
        return {
            "status": "fail",
            "message": (e.message if hasattr(e, 'message') else str(e)),
        }