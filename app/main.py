from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import card, item, sip, feig, tpad
import os, sys
from dotenv import load_dotenv


def get_env_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), ".env")
    return os.path.join(os.getcwd(), ".env")

load_dotenv(get_env_path())

load_dotenv()

app = FastAPI(title="RFIDCloud API", version="1.0")


def get_origins():
    origins = os.getenv("CORS_ORIGINS", "")
    origin_list = [o.strip() for o in origins.split(",") if o.strip()]

    if not origin_list:
        raise ValueError("CORS_ORIGINS is not set or empty")

    return origin_list


origins = get_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          
    allow_credentials=True,        
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(card.router, prefix="", tags=["Patron"])
app.include_router(feig.router, prefix="/feig", tags=["FEIG"])
app.include_router(tpad.router, prefix="/tpad", tags=["TPAD"])
# app.include_router(item.router, prefix="/Item", tags=["Item"])
# app.include_router(sip.router, prefix="/SIP", tags=["SIP"])