"""
AI 채팅 API 라우터
- 쇼핑 도우미 채팅, 레시피 검색, 채팅 히스토리
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.common import ApiResponse
from app.schemas.ai import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatLogOut,
    RecipeOut,
    AssociationOut,
)
from app.services import ai_service, ai_tools

router = APIRouter(prefix="/ai", tags=["AI 쇼핑 도우미"])


@router.post("/chat", response_model=ApiResponse[ChatMessageResponse])
async def chat(
    data: ChatMessageRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    AI 쇼핑 도우미와 대화합니다.

    지원하는 기능:
    - 상품 검색: "삼겹살 찾아줘", "우유 있어?"
    - 레시피 추천: "삼겹살 파티 레시피", "미역국 만들고 싶어"
    - 장바구니 관리: "장바구니 보여줘", "삼겹살 담아줘"
    - 가격 조회: "삼겹살 얼마야?", "할인 상품 뭐 있어?"
    - 연관 상품: "삼겹살이랑 뭐 같이 먹으면 좋아?"
    """
    result = await ai_service.process_chat(
        db=db,
        user_id=user_id,
        message=data.message,
        store_id=data.store_id,
    )
    return ApiResponse(data=result)


@router.get("/history", response_model=ApiResponse[list[ChatLogOut]])
async def get_history(
    limit: int = Query(20, ge=1, le=100, description="최근 N개 대화"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """최근 채팅 히스토리를 조회합니다."""
    logs = await ai_service.get_chat_history(db, user_id, limit)
    return ApiResponse(data=logs)


@router.get("/recipes", response_model=ApiResponse)
async def search_recipes(
    keyword: str = Query(..., description="레시피 검색 키워드"),
    db: AsyncSession = Depends(get_db),
):
    """
    레시피를 검색합니다 (인증 불필요).

    레시피명 또는 재료명으로 검색 가능합니다.
    """
    result = await ai_tools.execute_search_recipe(db, keyword)
    return ApiResponse(data=result)


@router.get("/associations/{product_id}", response_model=ApiResponse)
async def get_associations(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    연관 상품을 조회합니다 (인증 불필요).

    특정 상품과 함께 자주 구매되는 상품 목록을 반환합니다.
    """
    result = await ai_tools.execute_get_associations(db, product_id)
    return ApiResponse(data=result)


@router.get("/tools", response_model=ApiResponse)
async def list_tools():
    """
    AI 도우미가 사용 가능한 도구 목록을 조회합니다 (MCP 형식).

    개발/디버깅용 엔드포인트입니다.
    """
    return ApiResponse(data=ai_tools.TOOL_DEFINITIONS)
