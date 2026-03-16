"""
AI 채팅 관련 Pydantic 스키마
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ── 채팅 메시지 요청 ──
class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="사용자 메시지")
    store_id: Optional[UUID] = Field(None, description="매장 ID (상품/경로 관련 시 필요)")


# ── 도구 호출 결과 ──
class ToolCallResult(BaseModel):
    tool_name: str
    arguments: dict = {}
    result: dict = {}


# ── AI 추천 상품 ──
class AiRecommendation(BaseModel):
    product_id: UUID
    product_name: str
    reason: str = ""
    price: Optional[int] = None
    sale_price: Optional[int] = None


# ── AI 채팅 응답 ──
class ChatMessageResponse(BaseModel):
    message: str = Field(..., description="AI 응답 메시지")
    recommendations: list[AiRecommendation] = Field(default_factory=list, description="추천 상품 목록")
    cart_updates: list[dict] = Field(default_factory=list, description="장바구니 변경 사항")
    tool_calls: list[ToolCallResult] = Field(default_factory=list, description="실행된 도구 목록")
    session_id: Optional[UUID] = None


# ── 채팅 로그 조회 ──
class ChatLogOut(BaseModel):
    log_id: int
    role: str
    content: str
    tool_calls: Optional[list[dict]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── 레시피 응답 ──
class RecipeOut(BaseModel):
    recipe_id: int
    recipe_name: str
    description: Optional[str] = None
    difficulty: str
    cooking_time_min: Optional[int] = None
    servings: Optional[int] = None
    instructions: Optional[list[dict]] = None
    ingredients: list[dict] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ── 연관 상품 응답 ──
class AssociationOut(BaseModel):
    product_id: UUID
    product_name: str
    score: float
    reason: Optional[str] = None
