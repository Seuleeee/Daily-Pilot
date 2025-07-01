from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from api.schemas.base import Pagination, ResponseFormatSchema
from api.schemas.prompt import PromptCreate, PromptResponse, PromptUpdate

router = APIRouter(prefix="/prompts", tags=["Prompts"])

# 임시 인메모리 DB
SAMPLE_PROMPTS: list[PromptResponse] = [
    PromptResponse(
        id="1",
        title="Sample Prompt 1",
        content="This is a sample prompt.",
        description="설명1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    PromptResponse(
        id="2",
        title="Sample Prompt 2",
        content="Another prompt.",
        description="설명2",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
]


@router.get("/", response_model=ResponseFormatSchema[list[PromptResponse]])
async def get_prompts(page: int = 1, size: int = 10):
    """
    Get a list of prompts.
    """
    total = len(SAMPLE_PROMPTS)
    has_next = (page * size) < total
    pagination = Pagination(page=page, size=size, total=total, has_next=has_next)
    data = SAMPLE_PROMPTS[(page - 1) * size : page * size]
    return ResponseFormatSchema[list[PromptResponse]](
        status=200,
        message="프롬프트 목록 조회 성공",
        pagination=pagination,
        data=data,
    )


@router.get("/{prompt_id}", response_model=ResponseFormatSchema[PromptResponse])
async def get_prompt(prompt_id: str):
    for prompt in SAMPLE_PROMPTS:
        if prompt.id == prompt_id:
            return ResponseFormatSchema[PromptResponse](
                status=200,
                message="프롬프트 조회 성공",
                data=prompt,
            )
    raise HTTPException(status_code=404, detail="Prompt not found")


@router.post("/", response_model=ResponseFormatSchema[PromptResponse], status_code=status.HTTP_201_CREATED)
async def create_prompt(prompt: PromptCreate):
    new_prompt = PromptResponse(
        id=str(uuid4()),
        title=prompt.title,
        content=prompt.content,
        description=prompt.description,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    SAMPLE_PROMPTS.append(new_prompt)
    return ResponseFormatSchema[PromptResponse](
        status=201,
        message="프롬프트 생성 성공",
        data=new_prompt,
    )


@router.put("/{prompt_id}", response_model=ResponseFormatSchema[PromptResponse])
async def update_prompt(prompt_id: str, prompt_update: PromptUpdate):
    for idx, prompt in enumerate(SAMPLE_PROMPTS):
        if prompt.id == prompt_id:
            updated = prompt.copy(
                update={
                    **prompt_update.dict(exclude_unset=True),
                    "updated_at": datetime.now(),
                }
            )
            SAMPLE_PROMPTS[idx] = updated
            return ResponseFormatSchema[PromptResponse](
                status=200,
                message="프롬프트 수정 성공",
                data=updated,
            )
    raise HTTPException(status_code=404, detail="Prompt not found")


@router.delete("/{prompt_id}", response_model=ResponseFormatSchema[PromptResponse])
async def delete_prompt(prompt_id: str):
    for idx, prompt in enumerate(SAMPLE_PROMPTS):
        if prompt.id == prompt_id:
            deleted = SAMPLE_PROMPTS.pop(idx)
            return ResponseFormatSchema[PromptResponse](
                status=200,
                message="프롬프트 삭제 성공",
                data=deleted,
            )
    raise HTTPException(status_code=404, detail="Prompt not found")
