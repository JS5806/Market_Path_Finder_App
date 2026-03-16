"""
장바구니 서비스 - 세션 생성, 아이템 CRUD, 가격 합산
"""
from uuid import UUID
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.user import CartSession, CartItem
from app.models.product import Product, ProductPrice


async def create_cart_session(db: AsyncSession, user_id: UUID, store_id: Optional[UUID] = None) -> CartSession:
    """새 장바구니 세션 생성 (기존 active 세션이 있으면 그것을 반환)"""
    existing = await db.execute(
        select(CartSession)
        .options(selectinload(CartSession.items).selectinload(CartItem.product))
        .where(CartSession.user_id == user_id, CartSession.status == "active")
    )
    session = existing.scalar_one_or_none()
    if session:
        return session

    session = CartSession(user_id=user_id, store_id=store_id)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_active_cart(db: AsyncSession, user_id: UUID) -> Optional[CartSession]:
    """현재 활성 장바구니 세션 조회 (아이템 + 상품 정보 포함)"""
    result = await db.execute(
        select(CartSession)
        .options(selectinload(CartSession.items).selectinload(CartItem.product))
        .where(CartSession.user_id == user_id, CartSession.status == "active")
    )
    return result.scalar_one_or_none()


async def add_item_to_cart(
    db: AsyncSession,
    user_id: UUID,
    product_id: UUID,
    quantity: int = 1,
    source: str = "manual",
) -> CartItem:
    """장바구니에 아이템 추가 (같은 상품이면 수량 증가)"""
    # 활성 세션 확보
    session = await create_cart_session(db, user_id)

    # 상품 존재 확인
    prod_result = await db.execute(
        select(Product).where(Product.product_id == product_id, Product.is_active == True)
    )
    if not prod_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="상품을 찾을 수 없습니다")

    # 이미 장바구니에 있으면 수량 증가
    existing_item = await db.execute(
        select(CartItem).where(
            CartItem.session_id == session.session_id,
            CartItem.product_id == product_id,
        )
    )
    item = existing_item.scalar_one_or_none()

    if item:
        item.quantity += quantity
    else:
        item = CartItem(
            session_id=session.session_id,
            product_id=product_id,
            quantity=quantity,
            source=source,
        )
        db.add(item)

    await db.flush()
    await db.refresh(item)
    return item


async def update_item_quantity(db: AsyncSession, user_id: UUID, item_id: int, quantity: int) -> CartItem:
    """장바구니 아이템 수량 변경"""
    item = await _get_user_cart_item(db, user_id, item_id)
    item.quantity = quantity
    await db.flush()
    await db.refresh(item)
    return item


async def remove_item_from_cart(db: AsyncSession, user_id: UUID, item_id: int) -> None:
    """장바구니에서 아이템 제거"""
    item = await _get_user_cart_item(db, user_id, item_id)
    await db.delete(item)
    await db.flush()


async def clear_cart(db: AsyncSession, user_id: UUID) -> None:
    """장바구니 전체 비우기"""
    session = await get_active_cart(db, user_id)
    if not session:
        return
    for item in session.items:
        await db.delete(item)
    await db.flush()


async def build_cart_response(db: AsyncSession, session: CartSession, store_id: Optional[UUID] = None) -> dict:
    """장바구니 세션을 응답 형태로 변환 (가격 계산 포함)"""
    items_out = []
    total_price = 0

    for item in session.items:
        product = item.product
        # 가격 조회
        unit_price = 0
        if store_id or session.store_id:
            sid = store_id or session.store_id
            price_result = await db.execute(
                select(ProductPrice).where(
                    ProductPrice.product_id == item.product_id,
                    ProductPrice.store_id == sid,
                )
            )
            price = price_result.scalar_one_or_none()
            if price:
                unit_price = price.sale_price or price.regular_price

        subtotal = unit_price * item.quantity
        total_price += subtotal

        items_out.append({
            "item_id": item.item_id,
            "product_id": item.product_id,
            "product_name": product.product_name if product else "",
            "specification": product.specification if product else None,
            "quantity": item.quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
            "source": item.source,
            "is_collected": item.is_collected,
            "added_at": item.added_at,
        })

    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "store_id": session.store_id,
        "status": session.status,
        "items": items_out,
        "total_price": total_price,
        "item_count": len(items_out),
        "created_at": session.created_at,
    }


# ── 내부 헬퍼 ──
async def _get_user_cart_item(db: AsyncSession, user_id: UUID, item_id: int) -> CartItem:
    """사용자의 활성 장바구니에서 특정 아이템 가져오기"""
    result = await db.execute(
        select(CartItem)
        .join(CartSession)
        .where(
            CartSession.user_id == user_id,
            CartSession.status == "active",
            CartItem.item_id == item_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="장바구니 아이템을 찾을 수 없습니다")
    return item
