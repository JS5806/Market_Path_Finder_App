"""
결제 및 거래 로그 서비스
- QR 결제 페이로드 생성
- 결제 승인 처리
- 거래 내역 / 쇼핑 히스토리 기록 및 조회
"""
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Transaction
from app.models.user import CartSession, CartItem, ShoppingHistory
from app.models.product import Product, ProductPrice

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════
#  QR 결제 페이로드 생성
# ═══════════════════════════════════════

async def create_qr_payment(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    store_id: UUID,
) -> dict:
    """
    장바구니(CartSession)의 상품들로 QR 결제 데이터를 생성합니다.
    1) 장바구니 상품 조회 → 가격 계산
    2) Transaction 레코드 생성 (status=pending)
    3) QR 페이로드(JSON) 반환
    """
    # 장바구니 확인
    session_result = await db.execute(
        select(CartSession).where(
            CartSession.session_id == session_id,
            CartSession.user_id == user_id,
        )
    )
    cart_session = session_result.scalars().first()
    if not cart_session:
        raise ValueError("장바구니 세션을 찾을 수 없습니다.")

    # 장바구니 상품 조회
    items_result = await db.execute(
        select(CartItem).where(CartItem.session_id == session_id)
    )
    items = items_result.scalars().all()
    if not items:
        raise ValueError("장바구니가 비어 있습니다.")

    # 상품별 가격 계산
    total_amount = 0
    item_count = 0
    item_details = []

    for item in items:
        # 상품 정보
        prod_result = await db.execute(
            select(Product).where(Product.product_id == item.product_id)
        )
        product = prod_result.scalars().first()

        # 최신 가격
        price_result = await db.execute(
            select(ProductPrice)
            .where(
                ProductPrice.product_id == item.product_id,
                ProductPrice.store_id == store_id,
            )
            .order_by(ProductPrice.updated_at.desc())
            .limit(1)
        )
        price = price_result.scalars().first()

        if product and price:
            unit_price = int(price.sale_price) if price.sale_price else int(price.regular_price)
            line_total = unit_price * item.quantity
            total_amount += line_total
            item_count += item.quantity

            item_details.append({
                "product_id": str(item.product_id),
                "product_name": product.product_name,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            })

    # QR 페이로드 생성
    transaction_id = uuid.uuid4()
    qr_data = {
        "transaction_id": str(transaction_id),
        "store_id": str(store_id),
        "user_id": str(user_id),
        "total_amount": total_amount,
        "item_count": item_count,
        "items": item_details,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    qr_payload = json.dumps(qr_data, ensure_ascii=False)

    # Transaction 레코드 생성
    transaction = Transaction(
        transaction_id=transaction_id,
        user_id=user_id,
        session_id=session_id,
        store_id=store_id,
        total_amount=total_amount,
        payment_method="qr_code",
        qr_payload=qr_payload,
        status="pending",
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    return {
        "transaction_id": transaction_id,
        "qr_payload": qr_payload,
        "total_amount": total_amount,
        "item_count": item_count,
        "status": "pending",
        "created_at": transaction.created_at,
    }


# ═══════════════════════════════════════
#  결제 승인 (POS 시스템 호출)
# ═══════════════════════════════════════

async def confirm_payment(
    db: AsyncSession,
    transaction_id: UUID,
    approval_number: str,
) -> dict:
    """
    POS에서 QR을 스캔하고 결제를 승인할 때 호출합니다.
    1) Transaction 상태 → paid 로 업데이트
    2) CartSession 상태 → completed 로 업데이트
    3) ShoppingHistory 기록 생성
    """
    # 거래 조회
    result = await db.execute(
        select(Transaction).where(Transaction.transaction_id == transaction_id)
    )
    transaction = result.scalars().first()
    if not transaction:
        raise ValueError("거래를 찾을 수 없습니다.")

    if transaction.status == "paid":
        raise ValueError("이미 결제 완료된 거래입니다.")

    now = datetime.now(timezone.utc)

    # 거래 승인
    transaction.status = "paid"
    transaction.approval_number = approval_number
    transaction.paid_at = now

    # 장바구니 상태 변경
    session_result = await db.execute(
        select(CartSession).where(CartSession.session_id == transaction.session_id)
    )
    cart_session = session_result.scalars().first()
    if cart_session:
        cart_session.status = "completed"

    # 장바구니 상품 수 계산
    item_count_result = await db.execute(
        select(func.sum(CartItem.quantity)).where(
            CartItem.session_id == transaction.session_id
        )
    )
    item_count = item_count_result.scalar() or 0

    # 쇼핑 히스토리 기록
    history = ShoppingHistory(
        user_id=transaction.user_id,
        store_id=transaction.store_id,
        session_id=transaction.session_id,
        total_amount=transaction.total_amount,
        item_count=item_count,
        shopped_at=now,
    )
    db.add(history)

    await db.commit()

    return {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "approval_number": approval_number,
        "total_amount": transaction.total_amount,
        "paid_at": now,
    }


# ═══════════════════════════════════════
#  거래 내역 조회
# ═══════════════════════════════════════

async def get_transactions(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 20,
) -> list:
    """사용자의 거래 내역 (최근순)"""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_transaction_detail(
    db: AsyncSession,
    transaction_id: UUID,
    user_id: UUID,
) -> Optional[Transaction]:
    """거래 상세 조회"""
    result = await db.execute(
        select(Transaction).where(
            Transaction.transaction_id == transaction_id,
            Transaction.user_id == user_id,
        )
    )
    return result.scalars().first()


async def get_shopping_history(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 20,
) -> list:
    """사용자의 쇼핑 히스토리 (최근순)"""
    result = await db.execute(
        select(ShoppingHistory)
        .where(ShoppingHistory.user_id == user_id)
        .order_by(ShoppingHistory.shopped_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
