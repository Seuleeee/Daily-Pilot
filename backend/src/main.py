from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.v1 import api_router
from config.settings import get_settings

settings = get_settings()

SWAGGER_TITLE = "Daily Pilot API"
SWAGGER_DESCRIPTION = "Daily Pilot API Documentation"
SWAGGER_VERSION = "0.0.1"
SWAGGER_URL = "/docs"
SWAGGER_DOCS_URL = "/docs"
SWAGGER_REDOC_URL = "/redoc"


app = FastAPI(
    title=SWAGGER_TITLE,
    description=SWAGGER_DESCRIPTION,
    version=SWAGGER_VERSION,
    docs_url=SWAGGER_URL,
    redoc_url=SWAGGER_REDOC_URL,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
