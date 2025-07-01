from datetime import datetime

from pydantic import BaseModel, Field


class PromptBase(BaseModel):
    title: str = Field(..., description="Prompt title")
    content: str = Field(..., description="Prompt content")
    description: str | None = Field(None, description="Prompt description")


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    title: str | None = Field(None, description="Prompt title")
    content: str | None = Field(None, description="Prompt content")
    description: str | None = Field(None, description="Prompt description")


class PromptInDB(PromptBase):
    id: str = Field(..., description="Prompt ID")
    created_at: datetime = Field(..., description="Created timestamp")
    updated_at: datetime = Field(..., description="Updated timestamp")


class PromptResponse(PromptInDB):
    pass


class PromptListResponse(BaseModel):
    prompts: list[PromptResponse]
    total: int
