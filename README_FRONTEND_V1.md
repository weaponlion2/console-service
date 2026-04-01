# Frontend API Reference (ServiceCode)

This document is for frontend developers with clear API endpoint contract details.

## Base URL

`http://<host>:<port>` (example: `http://---HOST---:11102`)
current host - 192.168.1.30
---

## 1. Card routes

### POST /reader

Request JSON:
- reader (string)
- port (integer, default 0)

Success response:
- status (string), e.g. "success"
- readerstatus (string), e.g. "READER_CONNECTED"
- message (string), e.g. "ER302 Reader connected"
- output (any), usually null

Example request:
```
{ "reader": "CELRDR", "port": 0 }
```

Example response:
```
{
  "status": "success",
  "readerstatus": "READER_CONNECTED",
  "message": "ER302 Reader connected",
  "output": null
}
```

### POST /memory

Request JSON:
- cardtype (string, default "MIFARE")
- key (string, default "FFFFFFFFFFFF")
- block (int, default 0)
- length (int, default 32)

Success response:
- status (string), e.g. "success"
- readerstatus (string), e.g. "READ_SUCCESS"
- message (string), e.g. "Read completed"
- output (string), e.g. "A1B2C3..."

Example response:
```
{
  "status": "success",
  "readerstatus": "READ_SUCCESS",
  "message": "Block read complete",
  "output": "00112233445566778899AABBCCDDEEFF"
}
```

### PUT /memory

Request JSON:
- cardtype (string, default "MIFARE")
- key (string, default "FFFFFFFFFFFF")
- block (int, default 0)
- sessionid (string)
- data (string)

Success response:
- status (string), e.g. "success"
- readerstatus (string), e.g. "WRITE_SUCCESS"
- message (string), e.g. "Write completed"
- output (string), e.g. "100 bytes written"

Example response:
```
{
  "status": "success",
  "readerstatus": "WRITE_SUCCESS",
  "message": "Block write complete",
  "output": "A1B2C3..."
}
```

### GET /uid

No request body.

Success response:
- status (string), e.g. "success"
- readerstatus (string), e.g. "READ_UID_SUCCESS"
- message (string), e.g. "UID read"
- output (string), e.g. "04AABBCCDDEEFF"

Example response:
```
{
  "status": "success",
  "readerstatus": "READ_UID_SUCCESS",
  "message": "UID read",
  "output": "04AABBCCDDEEFF"
}
```

### POST /sectorkey

Request JSON:
- sector (int)
- current_key (string)
- new_key (string)
- keyB (string, optional)

Success response:
- status (string), e.g. "success"
- readerstatus (string), e.g. "KEY_CHANGED"
- message (string), e.g. "Sector key updated"

Example response:
```
{
  "status": "success",
  "readerstatus": "KEY_CHANGED",
  "message": "Sector key updated"
}
```

### GET /

Health check response:
- "Service is running"

Example response:
```
Service is running
```

### POST /login

Success response:
- sessionid (string), example: "5pPS0Tc..."
- status: "success"
- updaterequired: false

Example response:
```
{
  "sessionid": "5pPS0Tc5kUOTr1HPARhHoSh18pSqXMJWB1/3/pFL1TlPqAl74DzJS2RF2/fDJttTpM1dcz/d0+oNbWx+TYNSdQ==",
  "status": "success",
  "updaterequired": false
}
```

### GET /serialkey

Success response:
- status: "success"
- serial_key (string)

Example success response:
```
{
  "status": "success",
  "serial_key": "<encrypted-key-string>"
}
```

Error response:
- status: "fail"
- message (string)

### POST /str-to-hex

Request JSON:
- data (string)

Success response:
- value (string, hex)
- status: "success"

Example:
```
Request: { "data": "hello" }
Response: { "value": "68656C6C6F", "status": "success" }
```

Error response:
- status: "fail"
- message (string)

### POST /hex-to-str

Request JSON:
- data (string, hex)

Success response:
- value (string)
- status: "success"

Example:
```
Request: { "data": "48656C6C6F" }
Response: { "value": "Hello", "status": "success" }
```

Error response:
- status: "fail"
- message (string)

---


## Usage notes

- All JSON request bodies are content-type `application/json`.
- Validate required fields before sending to avoid HTTP Error.

## Available Readers, Status, and ReaderStatus

### reader (supported values)
- `CELRDR` (ER302 reader)
- `HIDOK` (HID reader)

### status (from API)
- `success`
- `fail`

### readerstatus (common values)
- `READER_CONNECTED`
- `NOT_CONNECTED`
- `NO_READER`
- `KEY_CHANGED`
- `KEY_CHANGE_FAILED`
- `READ_SUCCESS`
- `WRITE_SUCCESS`
- `READ_UID_SUCCESS`
- `PROCESS_ERROR`
