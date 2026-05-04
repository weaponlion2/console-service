import platform 
import subprocess, re
from typing import Optional


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
                with open("/sys/class/dmi/id/board_vendor") as f:
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
                with open("/sys/class/dmi/id/board_name") as f:
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

