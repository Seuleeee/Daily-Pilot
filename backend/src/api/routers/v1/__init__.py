from fastapi import APIRouter

from api.routers.v1.endpoints.prompt import router as prompts_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(prompts_router)
