import sys
import serial.tools.list_ports


CP2102_VID = 0x10C4
CP2102_PID = 0xEA60


def find_cp2102(debug: bool = False):
    ports = list(serial.tools.list_ports.comports())

    if debug:
        print("\n🔍 Detected Ports:")
        for p in ports:
            print(f"""
            Device      : {p.device}
            Description : {p.description}
            HWID        : {p.hwid}
            VID:PID     : {p.vid}:{p.pid}
            """)

    # ✅ Primary: VID/PID match (works on Windows, Linux, macOS)
    matches = [
        p.device for p in ports
        if p.vid == CP2102_VID and p.pid == CP2102_PID
    ]

    if matches:
        # If multiple, return first (or change logic if needed)
        return matches[0]

    # ⚠️ Fallback (only if VID/PID not available)
    for p in ports:
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()

        if "cp2102" in desc or "silicon labs" in desc or "cp210x" in hwid:
            return p.device

    return None