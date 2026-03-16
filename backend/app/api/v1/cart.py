"""
장바구니 API 라우터
- 세션 생성, 아이템 추가/수정/삭제, 장바구니 조회
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.common import ApiResponse
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartSessionOut, CartSessionCreate
from app.services import cart_service

router = APIRouter(prefix="/cart", tags=["장바구니"])


@router.post("/session", response_model=ApiResponse[CartSessionOut])
async def create_or_get_session(
    data: CartSessionCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """장바구니 세션 생성 (이미 활성 세션이 있으면 기존 세션 반환)"""
    session = await cart_service.create_cart_session(db, user_id, data.store_id)
    resp = await cart_service.build_cart_response(db, session)
    return ApiResponse(data=resp)


@router.get("", response_model=ApiResponse[CartSessionOut])
async def get_my_cart(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """현재 활성 장바구니 조회"""
    session = await cart_service.get_active_cart(db, user_id)
    if not session:
        return ApiResponse(success=False, message="활성 장바구니가 없습니다", data=None)
    resp = await cart_service.build_cart_response(db, session)
    return ApiResponse(data=resp)


@router.post("/items", response_model=ApiResponse)
async def add_item(
    data: CartItemAdd,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """장바구니에 아이템 추가"""
    item = await cart_service.add_item_to_cart(
        db, user_id, data.product_id, data.quantity, data.source
    )
    return ApiResponse(message="장바구니에 추가되었습니다", data={"item_id": item.item_id})


@router.patch("/items/{item_id}", response_model=ApiResponse)
async def update_item(
    item_id: int,
    data: CartItemUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """장바구니 아이템 수량 변경"""
    await cart_service.update_item_quantity(db, user_id, item_id, data.quantity)
    return ApiResponse(message="수량이 변경되었습니다")


@router.delete("/items/{item_id}", response_model=ApiResponse)
async def remove_item(
    item_id: int,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """장바구니에서 아이템 제거"""
    await cart_service.remove_item_from_cart(db, user_id, item_id)
    return ApiResponse(message="아이템이 제거되었습니다")


@router.delete("/clear", response_model=ApiResponse)
async def clear_all_items(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """장바구니 전체 비우기"""
    await cart_service.clear_cart(db, user_id)
    return ApiResponse(message="장바구니가 비워졌습니다")
