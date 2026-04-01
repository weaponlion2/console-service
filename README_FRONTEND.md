# Frontend API Reference (ServiceCode)

This document is for frontend developers with clear API endpoint contract details.

## Base URL

`http://<host>:<port>` (example: `http://localhost:8000`)

---

## 1. Card routes

### POST /reader

Request JSON:
- reader (string)
- port (integer, default 0)

Success response:
- status (string)
- readerstatus (string)
- message (string)
- output (any)

Example:
```
{ "reader": "COM3", "port": 0 }
```

### POST /memory

Request JSON:
- cardtype (string, default "MIFARE")
- key (string, default "FFFFFFFFFFFF")
- block (int, default 0)
- length (int, default 32)

Success response:
- status (string)
- readerstatus (string)
- message (string)
- output (any)

### PUT /memory

Request JSON:
- cardtype (string, default "MIFARE")
- key (string, default "FFFFFFFFFFFF")
- block (int, default 0)
- sessionid (string)
- data (string)

Success response:
- status (string)
- readerstatus (string)
- message (string)
- output (any)

### GET /uid

No request body.

Success response:
- status (string)
- uid (string) or output

### POST /sectorkey

Request JSON:
- sector (int)
- current_key (string)
- new_key (string)
- keyB (string, optional)

Success response:
- status (string)
- readerstatus (string)
- message (string)

### GET /

Health check response:
- "Service is running"

### POST /login

Response:
- sessionid (string)
- status: "success"
- updaterequired (boolean)

### GET /serialkey

Success response:
- status: "success"
- serial_key (string)

Error response:
- status: "fail"
- message (string)

### POST /str-to-hex

Request JSON:
- data (string)

Success response:
- value (string, hex)
- status: "success"

Error response:
- status: "fail"
- message (string)

### POST /hex-to-str

Request JSON:
- data (string, hex)

Success response:
- value (string)
- status: "success"

Error response:
- status: "fail"
- message (string)

---

## 2. Item route

### POST /

Request JSON:
- reader (string)
- port (int, default 0)
- command (string)
- input (string)
- secure (string, optional)
- afi (string, optional)

Success response:
- status (string)
- readerstatus (string)
- message (string)
- output (any)
- easstatus (string)
- afi (string)

---

## 3. SIP routes

Common object: sipinfo
- host (string)
- port (string)
- user (string)
- password (string)
- loccd (string, optional)
- libid (string, optional)

### POST /Patron

Request JSON:
- patronid (string)
- pin (string)
- sipinfo (object)

Response:
- status (string)
- message (string)
- issueditems (array)
- patron (object)

### POST /Item

Request JSON:
- itemid (string)
- sipinfo (object)

Response:
- status (string)
- message (string)
- itemid (string)
- itemstatus (string)
- statuscd (string)
- title (string)

### POST /Checkout

Request JSON:
- patronid (string)
- pin (string)
- itemid (string)
- sipinfo (object)

Response:
- status (string)
- message (string)

### POST /Checkin

Request JSON:
- itemid (string)
- sipinfo (object)

Response:
- status (string)
- message (string)

---

## 4. SIP/reader helper routes

### GET /uid

Params/Request JSON:
- reader (string)
- key (string, default "FFFFFFFFFFFF")

### GET /memory

Params/Request JSON:
- reader (string)
- block (int, default 1)
- length (int, default 32)
- key (string, default "FFFFFFFFFFFF")
- write (optional object)

### POST /memory

Request JSON: same as GET /memory.

### POST /secure

Request JSON:
- reader (string)
- sector (int, default 0)
- current_key (string, default "FFFFFFFFFFFF")
- new_key (string)
- keyB (string, optional)

---

## Usage notes

- All JSON request bodies are content-type `application/json`.
- Validate required fields before sending to avoid HTTP 422.
