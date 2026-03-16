"""
장바구니 관련 Pydantic 스키마
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ── 장바구니 아이템 추가 요청 ──
class CartItemAdd(BaseModel):
    product_id: UUID
    quantity: int = Field(1, ge=1, le=99)
    source: str = Field("manual", pattern="^(manual|ai|nfc)$")


# ── 장바구니 아이템 수량 수정 ──
class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, le=99)


# ── 장바구니 아이템 응답 ──
class CartItemOut(BaseModel):
    item_id: int
    product_id: UUID
    product_name: str = ""
    specification: Optional[str] = None
    quantity: int
    unit_price: int = 0          # 현재가 (할인 적용)
    subtotal: int = 0            # unit_price * quantity
    source: str
    is_collected: bool
    added_at: datetime

    model_config = {"from_attributes": True}


# ── 장바구니 세션 응답 ──
class CartSessionOut(BaseModel):
    session_id: UUID
    user_id: UUID
    store_id: Optional[UUID] = None
    status: str
    items: list[CartItemOut] = []
    total_price: int = 0
    item_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# ── 장바구니 세션 생성 요청 ──
class CartSessionCreate(BaseModel):
    store_id: Optional[UUID] = None
