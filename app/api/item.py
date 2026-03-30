from fastapi import APIRouter
from app.schemas.item import ItemRequest
from app.services.item_service import ItemService
from app.integrations.reader_client import ReaderClient

router = APIRouter()
service = ItemService(ReaderClient())

@router.post("/")
def item(request: ItemRequest):
    return service.process_item(request)
