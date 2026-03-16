"""
공통 응답 스키마
"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """통일된 API 응답 래퍼"""
    success: bool = True
    message: str = "ok"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 응답"""
    items: list[T] = []
    total: int = 0
    page: int = 1
    size: int = 20
    pages: int = 0
