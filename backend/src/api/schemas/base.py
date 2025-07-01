from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Pagination(BaseModel):
    page: int = Field(..., description="페이지 번호")
    size: int = Field(..., description="페이지 크기")
    total: int = Field(..., description="총 데이터 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")


class ResponseFormatSchema(BaseModel, Generic[T]):
    status: int = Field(..., description="HTTP 상태 코드")
    message: str = Field(..., description="응답 메시지")
    pagination: Pagination | None = None
    data: T | None = Field(None, description="응답 데이터")
