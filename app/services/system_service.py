import platform
import uuid
import subprocess
import hashlib
import base64, re
from typing import Optional, Dict

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF1
from Crypto.Util.Padding import pad


# =============================
# C# ENCRYPTION CONFIG (MUST MATCH)
# =============================

PASSPHRASE = "D4i5w6e7s8H9"
SALT = b"ZEDON"
ITERATIONS = 2
KEY_SIZE = 32  # 256-bit
IV = b"@1B2c3D4e5F6g7H8"

APP_CODE = "RFIDCloud"
PRODUCT_NAME = "RFID Cloud Service"


# =============================
# UTILITIES
# =============================

BAD_VALUES = {
    "", "none", "unknown", "default string",
    "to be filled by o.e.m.", "system manufacturer"
}


def clean_value(value: Optional[str], default: str) -> str:
    if not value:
        return default

    value = value.strip()

    if value.lower() in BAD_VALUES:
        return default

    return value


def normalize(s: str) -> str:
    """Remove non-alphanumeric characters and convert to uppercase."""
    return re.sub(r'[^A-Za-z0-9]', '', s).upper()


def run_powershell(command: str | list[str]) -> Optional[str]:
    try:         
        if platform.system() == "Windows":             
            result = subprocess.run(                 
                ["powershell", "-NoProfile", "-Command", command],                 
                capture_output=True,                 
                text=True,                 
                timeout=3             
                )             
            if result.returncode == 0:                 
                lines = result.stdout.strip().splitlines()                 
                return lines[-1].strip() if lines else None         
            else:             
                return subprocess.check_output(                 
                    command,                 
                    text=True             
                    ).strip()          
    except:         
        return None



# =============================
# HARDWARE INFO
# =============================

class HardwareInfo:

    @staticmethod
    def get_manufacturer() -> str:
        if platform.system() == "Windows":
            value = run_powershell(
                "(Get-CimInstance Win32_ComputerSystem).Manufacturer"
            )
            return clean_value(value, "Unknown")

        elif platform.system() == "Linux":
            try:
                with open("/sys/class/dmi/id/sys_vendor") as f:
                    return clean_value(f.read(), "Unknown")
            except:
                pass

        return "Unknown"

    @staticmethod
    def get_model() -> str:
        if platform.system() == "Windows":
            value = run_powershell(
                "(Get-CimInstance Win32_BaseBoard).Product"
            )
            return clean_value(value, platform.machine())

        elif platform.system() == "Linux":
            try:
                with open("/sys/class/dmi/id/product_name") as f:
                    return clean_value(f.read(), platform.machine())
            except:
                pass

        return platform.machine()

    @staticmethod
    def get_serial() -> str:
        value = None
        if platform.system() == "Windows":
            value = run_powershell(
                "(Get-CimInstance Win32_Processor).ProcessorId"
            )
            value = clean_value(value, "")
            if not value:
                value = run_powershell(
                    "(Get-CimInstance Win32_DiskDrive).SerialNumber"
                )
                value = clean_value(value, "")

        elif platform.system() == "Linux":
            commands = [
                ["lsblk", "-dn", "-o", "SERIAL", "/dev/sda"],
                ["lsblk", "-dn", "-o", "SERIAL"]
            ]
            for cmd in commands:
                try:
                    value = run_powershell(
                        cmd                    
                        )
                    value = clean_value(value, "")
                    if value:
                        break
                except:                    
                    pass
            
        return value or ""


# =============================
# HEX UTILS
# =============================


def to_hex_string(s: str) -> str:
    """Convert string to uppercase hex representation (ASCII bytes)."""
    return s.encode('ascii').hex().upper()


def from_hex_string(value: str) -> str:
    return bytes.fromhex(value).decode("utf-8")


def unpad(data: bytes) -> bytes:
    return data[:-data[-1]]



def derive_key_passwordderivebytes(passphrase: str, salt: bytes, iterations: int, key_length: int) -> bytes:
    """
    Microsoft PasswordDeriveBytes implementation (non-standard PBKDF1 extension).
    
    Critical: .NET PasswordDeriveBytes encodes the passphrase string as UTF-16LE (Unicode).
    """
    # UTF-16LE encoding for passphrase (matches .NET PasswordDeriveBytes behavior)
    password_bytes = passphrase.encode('utf-16-le')
    
    # Generate first 20-byte block (SHA1 output size)
    hash_bytes = hashlib.sha1(password_bytes + salt).digest()
    for _ in range(1, iterations):
        hash_bytes = hashlib.sha1(hash_bytes).digest()
    
    key = hash_bytes
    
    # Generate additional blocks if key_length > 20 bytes
    counter = 1
    while len(key) < key_length:
        # Counter as 4-byte big-endian integer (matches .NET behavior)
        data = hash_bytes + counter.to_bytes(4, byteorder='big')
        block = hashlib.sha1(data).digest()
        for _ in range(1, iterations):
            block = hashlib.sha1(block).digest()
        key += block
        counter += 1
    
    return key[:key_length]


def encrypt(plain_text: str) -> str:
    """Encrypt plaintext using AES-256-CBC with PKCS7 padding, base64 output."""
    key = derive_key_passwordderivebytes(PASSPHRASE, SALT, ITERATIONS, KEY_SIZE)
    cipher = AES.new(key, AES.MODE_CBC, IV)
    padded = pad(plain_text.encode('utf-8'), AES.block_size)  # PKCS7 padding (matches .NET default)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode('ascii')

def decrypt(cipher_text: str) -> str:
    key = derive_key_passwordderivebytes()
    cipher = AES.new(key, AES.MODE_CBC, IV)

    decrypted = cipher.decrypt(base64.b64decode(cipher_text))
    return unpad(decrypted).decode()


# =============================
# SERIAL KEY GENERATION
# =============================

def generate_serial_key() -> str:
    """Generate encrypted serial key matching C# logic."""
    make = normalize(HardwareInfo.get_manufacturer())
    model = normalize(HardwareInfo.get_model())
    serial = normalize(HardwareInfo.get_serial())
    
    print("Hardware info collected:")
    print(f"  Manufacturer: {make}")
    print(f"  Model: {model}")
    print(f"  Serial: {serial}")
    
    raw = "{}:{}:{}:{}".format(
        to_hex_string(make),
        to_hex_string(model),
        to_hex_string(serial),
        to_hex_string(APP_CODE)
    )
    # print(f"Generated raw serial key data: {raw}")
    
    return (raw)


# =============================
# VALIDATION
# =============================

def validate_serial_key(serial_key: str) -> Dict[str, str]:
    try:
        decrypted = decrypt(serial_key)

        parts = decrypted.split(":")

        if len(parts) != 4:
            raise ValueError("Invalid format")

        make = from_hex_string(parts[0])
        model = from_hex_string(parts[1])
        serial = from_hex_string(parts[2])
        app_code = from_hex_string(parts[3])

        if app_code != APP_CODE:
            raise ValueError("Invalid app code")

        current_make = normalize(HardwareInfo.get_manufacturer())
        current_model = normalize(HardwareInfo.get_model())
        current_serial = normalize(HardwareInfo.get_serial())

        if [make, model, serial] != [current_make, current_model, current_serial]:
            raise ValueError("Device mismatch")

        return {
            "status": "valid",
            "manufacturer": make,
            "model": model,
            "serial": serial
        }

    except Exception as e:
        return {
            "status": "invalid",
            "error": str(e)
        }