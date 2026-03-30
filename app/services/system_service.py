import os
import platform
import uuid
from app.services.encrypt_service import encrypt


def to_hex_string(value: str) -> str:
    return value.encode('utf-8').hex()

def get_manufacturer():
    try:
        with open("/sys/class/dmi/id/sys_vendor", "r") as f:
            return f.read().strip()
    except:
        return "UnknownManufacturer"

def get_model():
    try:
        with open("/sys/class/dmi/id/product_name", "r") as f:
            return f.read().strip()
    except:
        return platform.machine()

def get_serial():
    try:
        with open("/sys/class/dmi/id/product_serial", "r") as f:
            return f.read().strip()
    except:
        return str(uuid.getnode())


def generate_serial_key():
    make = get_manufacturer()
    model = get_model()
    serial = get_serial()
    app_code = "RFID Cloud Service"  # Application.ProductName equivalent

    raw_string = "{}:{}:{}:{}".format(
        to_hex_string(make),
        to_hex_string(model),
        to_hex_string(serial),
        to_hex_string(app_code)
    )

    encrypted = encrypt(raw_string)
    return encrypted
