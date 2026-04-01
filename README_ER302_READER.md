# ER302 Reader Integration Guide

A guide for integrating and maintaining the `ER302_Reader` class used for RFID communication.

---

# 1. Overview

`ER302_Reader` is a Python class that provides a structured interface for interacting with an ER302 RFID reader over serial communication.

It supports:

* Reader initialization
* Card detection and UID retrieval
* Block-level authentication
* Memory read/write operations
* Sector key management

This class abstracts low-level protocol handling (checksum, escaping, packet structure).

---

# 2. Requirements

## Python dependencies

```bash
pip install pyserial
```

## Hardware

* ER302 RFID Reader (UART/USB)
* MIFARE Classic compatible cards (1K/4K)

## OS Support

* Linux (recommended)
* Example port:

  ```
  /dev/serial/by-id/...
  ```

---

# 3. Quick Start

```python
from ER302_Reader import ER302_Reader

reader = ER302_Reader("/dev/ttyUSB0", 9600)

if not reader.open():
    raise Exception("Failed to open serial port")

if not reader.init_reader():
    raise Exception("Failed to initialize reader")

uid_response = reader.read_uid()
print(uid_response)
```

---

# 4. Core Concepts

## Blocks & Sectors

* Each block = 16 bytes
* Sectors:

  * 0–31 → 4 blocks each
  * 32–39 → 16 blocks each
* Last block in sector = **trailer block** (contains keys & access bits)

⚠️ Trailer blocks cannot be written using normal write operations.

---

# 5. Payload Schemas

## Read Memory

```json
{
  "key": "FFFFFFFFFFFF",
  "block": 0,
  "length": 32
}
```

## Write Memory

```json
{
  "key": "FFFFFFFFFFFF",
  "block": 0,
  "data": "48656C6C6F"
}
```

* `data` can be:

  * Hex string (preferred)
  * List of byte integers

## Change Sector Key

```json
{
  "sector": 1,
  "current_key": "FFFFFFFFFFFF",
  "new_key": "A1A2A3A4A5A6",
  "keyB": "FFFFFFFFFFFF"
}
```

---

# 6. Public APIs

## read_uid()

Returns:

```json
{
  "status": true,
  "data": "A1B2C3D4",
  "readerstatus": "CARD_VALID"
}
```

---

## read_memory(payload)

* Authenticates and reads blocks
* Skips trailer blocks automatically

Success:

```json
{
  "status": true,
  "data": "HEX_STRING",
  "readerstatus": "CARD_VALID"
}
```

---

## write_memory(payload)

* Writes data across multiple blocks
* Automatically pads to 16-byte boundaries

Success:

```json
{
  "status": true,
  "readerstatus": "WRITE_SUCCESS"
}
```

---

## change_sector_key(payload)

* Updates sector Key A
* Preserves access bits

Success:

```json
{
  "status": true,
  "readerstatus": "KEY_CHANGED"
}
```

---

# 7. Reader Status Codes

## Success

* `CARD_VALID`
* `WRITE_SUCCESS`
* `KEY_CHANGED`

## Retryable Errors

* `NO_CARD`
* `ANTICOLL_FAIL`

## Fatal Errors

* `AUTH_FAILED`
* `READ_FAILED`
* `BAD_REQUEST`
* `FAILED_TO_WRITE_BLOCK`
* `KEY_CHANGE_FAILED`

---

# 8. Serial Protocol (Advanced)

## Packet Structure

```
[0xAA, 0xBB, LEN, 0x00, DEV_ID(2), CMD(2), PARAMS..., CHECKSUM]
```

## Checksum

* XOR of:

  * Device ID
  * Command
  * Status/Data

## Escaping Rule

* If byte == `0xAA`
* Append extra `0x00`

---

# 9. Internal Architecture

```
Application Layer
        ↓
ReaderClient
        ↓
ER302_Reader
        ↓
Serial Communication
        ↓
RFID Hardware
```

---

# 10. Best Practices

* Always call `init_reader()` before operations
* Avoid writing trailer blocks directly
* Validate payloads before calling APIs
* Handle retryable errors with backoff
* Log raw packets when debugging (`_send_cmd`, `_recv_resp`)

---

# 11. Common Issues

## Reader not detected

* Check USB connection
* Verify serial path

## Authentication failure

* Incorrect key
* Sector locked

## Partial reads/writes

* Block alignment issue
* Insufficient space

---

# 12. Notes

* Keep `readerstatus` values stable for API consumers
* Designed for backend integration (not UI-facing)
* Extend carefully when modifying protocol logic

---

# 13. Summary

This module provides a reliable abstraction over ER302 RFID communication, enabling safe and structured interaction with card memory while handling protocol-level complexity internally.
