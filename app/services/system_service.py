import platform
import uuid
import subprocess
from typing import Optional, Dict

from app.services.encrypt_service import encrypt, decrypt


# -----------------------------
# Utilities
# -----------------------------

BAD_VALUES = {
    "", "none", "unknown", "default string",
    "to be filled by o.e.m.", "system manufacturer"
}


def clean_value(value: Optional[str], default: str) -> str:
    if not value:
        return default

    value = value.strip().lower()

    if value in BAD_VALUES:
        return default.lower()

    return value


def normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def run_powershell(command: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=3
        )
        if result.returncode == 0:
            lines = result.stdout.strip().splitlines()
            return lines[-1].strip() if lines else None
    except:
        pass
    return None


# -----------------------------
# Hardware Info (Cross-platform)
# -----------------------------

class HardwareInfo:

    @staticmethod
    def get_manufacturer() -> str:
        if platform.system() == "Windows":
            value = run_powershell(
                "(Get-CimInstance Win32_ComputerSystem).Manufacturer"
            )
            return clean_value(value, "unknown")

        elif platform.system() == "Linux":
            try:
                with open("/sys/class/dmi/id/sys_vendor") as f:
                    return clean_value(f.read(), "unknown")
            except:
                pass

        return "unknown"

    @staticmethod
    def get_model() -> str:
        if platform.system() == "Windows":
            value = run_powershell(
                "(Get-CimInstance Win32_ComputerSystem).Model"
            )
            return clean_value(value, platform.machine())

        elif platform.system() == "Linux":
            try:
                with open("/sys/class/dmi/id/product_name") as f:
                    return clean_value(f.read(), platform.machine())
            except:
                pass

        return platform.machine().lower()

    @staticmethod
    def get_serial() -> str:
        if platform.system() == "Windows":
            value = run_powershell(
                "(Get-CimInstance Win32_BIOS).SerialNumber"
            )
            value = clean_value(value, "")
            if value:
                return value

        elif platform.system() == "Linux":
            try:
                with open("/sys/class/dmi/id/product_serial") as f:
                    return clean_value(f.read(), "")
            except:
                pass

        # fallback
        return str(uuid.getnode())


# -----------------------------
# Fingerprint
# -----------------------------

def generate_fingerprint() -> str:
    make = normalize(HardwareInfo.get_manufacturer())
    model = normalize(HardwareInfo.get_model())
    serial = normalize(HardwareInfo.get_serial())

    return f"{make}|{model}|{serial}"


# -----------------------------
# Serial Key
# -----------------------------

APP_CODE = "rfid-cloud-service"


def generate_serial_key() -> str:
    fingerprint = generate_fingerprint()

    raw = f"{fingerprint}|{APP_CODE}"

    return encrypt(raw)


# -----------------------------
# Validation
# -----------------------------

def validate_serial_key(serial_key: str) -> Dict[str, str]:
    try:
        decrypted = decrypt(serial_key)

        parts = decrypted.split("|")

        if len(parts) != 4:
            raise ValueError("Invalid format")

        make, model, serial, app_code = parts

        if app_code != APP_CODE:
            raise ValueError("Invalid app code")

        current_fp = generate_fingerprint().split("|")

        if [make, model, serial] != current_fp:
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