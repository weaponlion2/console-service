from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import card, item, sip

app = FastAPI(title="RFIDCloud API", version="1.0")

origins = [
    "http://localhost:5001", 
    "http://localhost:6001", 
    "http://localhost:7001", 
    "http://localhost:8001", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Specific origins (recommended)
    allow_credentials=True,
    allow_methods=["*"],            # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],            # Authorization, Content-Type, etc.
)


app.include_router(card.router, prefix="", tags=["Patron"])
app.include_router(item.router, prefix="/Item", tags=["Item"])
app.include_router(sip.router, prefix="/SIP", tags=["SIP"])
