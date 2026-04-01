# Backend Developer API Guide (ServiceCode)

This file explains why each service method exists, what input it takes, and what output it produces. It is aimed at backend developers who need to maintain and extend the API stack.

## 1. Architecture overview

- `app/main.py`: FastAPI app registration and CORS policy.
- `app/api/*`: API route definitions that call service layer.
- `app/services/*`: Business logic glue between API and integration clients.
- `app/integrations/*`: Reader/SIP low-level clients and underlying hardware protocol.
- `app/schemas/*`: Pydantic request/response models.

---

## 2. Schemas (app/schemas)

### app/schemas/card.py
- `ReaderRequest`: `reader` (str), `port` (int)
- `MemoryRequest`: `cardtype` (str), `key` (str), `block` (int), `length` (int)
- `MemoryUpdateRequest`: `cardtype`, `key`, `block`, `sessionid`, `data`
- `SecureSectorRequest`: `sector`, `current_key`, `new_key`, `keyB` (opt)
- `HexStringRequest`: `data` (str)

---

## 3. CardService (app/services/card_service.py)

### init_reader(request: ReaderRequest)
- Why: initialize reader and make it ready for all card operations.
- Input: `ReaderRequest`
- Calls: `ReaderClient.init_reader`.
- Output model:
  - `status` ("success"/"fail")
  - `readerstatus`
  - `message`

### read_memory(request: MemoryRequest)
- Why: read memory from card block.
- Input: `MemoryRequest`
- Calls: `ReaderClient.readMemory`.
- Output model:
  - `status`, `readerstatus`, `message`, `output`

### write_memory(request: MemoryUpdateRequest)
- Why: write data to card block.
- Input: `MemoryUpdateRequest`
- Calls: `ReaderClient.writeMemory`.
- Output model:
  - `status`, `readerstatus`, `message`, `output`

### read_uid()
- Why: read unique card identifier.
- Input: none
- Calls: `ReaderClient.readUID`.
- Output model: `status`, `readerstatus`, `message`, `output`

### change_sector_key(request: SecureSectorRequest)
- Why: change a sector key used for authentication.
- Input: `SecureSectorRequest`
- Calls: `ReaderClient.changeSectorKey`.
- Output model: `status`, `readerstatus`, `message`, `output`

---

## 4. ReaderClient (app/integrations/reader_client.py) request/response behavior

### init_reader
- Request body: `{"reader": "CELRDR" | "HIDOK", "port": 0}`
- Successful:
  - `status`: "success"
  - `readerstatus`: "READER_CONNECTED"
  - `message`: "ER302 Reader connected" or "Hid Reader connected"
  - `reader`: object

- Failure:
  - `status`: "fail"
  - `readerstatus`: e.g. "NO_READER", "NOT_CONNECTED", "READER_INVALID"
  - `message`: text
  - `reader`: null

### readMemory
- Request body example: `{"reader": "CELRDR", "block": 1, "length": 32, "key": "FFFFFFFFFFFF"}`
- Success output:
  - `status`: "success"
  - `readerstatus`: e.g. "READ_SUCCESS"
  - `message`, `output` (hex/text)

### writeMemory
- Request: `{"reader": "CELRDR", "block": 1, "key": "FFFFFFFFFFFF", "data": "..."}`
- Success output: status, readerstatus, message, output

### changeSectorKey
- Request: `{"reader": "CELRDR", "sector": 1, "current_key": "FFFFFFFFFFFF", "new_key": "A0A1A2A3A4A5"}`
- Output: status, readerstatus, message

### readUID
- Request: no payload (reader must be initialized)
- Success output: `status`, `readerstatus`, `message`, `output` (UID)

---

## 5. generate_serial_key / system info
- `generate_serial_key()` uses manufacturer/model/serial + app code via `encrypt()`.
- Output: encrypted serial key string.

---

## 6. Endpoint -> Service mapping (same as routes)

- `/reader` -> `CardService.init_reader`
- `/memory` (POST) -> `CardService.read_memory`
- `/memory` (PUT) -> `CardService.write_memory`
- `/uid` -> `CardService.read_uid`
- `/sectorkey` -> `CardService.change_sector_key`

---

## 9. Available readers/status/readerstatus

- `reader`: `CELRDR`, `HIDOK`
- `status`: `success`, `fail`
- `readerstatus`: `READER_CONNECTED`, `NOT_CONNECTED`, `NO_READER`, `KEY_CHANGED`, `KEY_CHANGE_FAILED`, `READ_SUCCESS`, `WRITE_SUCCESS`, `READ_UID_SUCCESS`, `PROCESS_ERROR`

---

## 10. Quick troubleshooting

- 422: schema validation time; ensure request matches model.
- `NO_READER`: call `/reader` first.
- `PROCESS_ERROR`: inspect node logs and reader availability.

