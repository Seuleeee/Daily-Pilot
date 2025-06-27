from fastapi import APIRouter

router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.get("/")
async def get_prompts():
    """
    Get a list of prompts.
    """
    return {"message": "Hello, world!"}
