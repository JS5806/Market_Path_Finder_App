"""
결제 및 거래 내역 API 엔드포인트
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.payment import (
    QrPaymentRequest, QrPaymentOut,
    PaymentConfirmRequest, PaymentConfirmOut,
    TransactionOut, ShoppingHistoryOut,
)
from app.services import payment_service

router = APIRouter(prefix="/payment", tags=["결제"])


# ═══════════════════════════════════════
#  QR 결제 생성
# ═══════════════════════════════════════

@router.post("/qr-generate", response_model=QrPaymentOut, summary="QR 결제 생성")
async def generate_qr_payment(
    req: QrPaymentRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    장바구니의 상품들로 QR 결제 데이터를 생성합니다.
    - 장바구니 상품 가격을 합산하여 총액 계산
    - QR 코드에 인코딩할 JSON 페이로드 생성
    - Transaction 레코드 (status=pending) 생성
    """
    try:
        result = await payment_service.create_qr_payment(
            db=db,
            user_id=user_id,
            session_id=req.session_id,
            store_id=req.store_id,
        )
        return QrPaymentOut(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════
#  결제 승인
# ═══════════════════════════════════════

@router.post("/confirm", response_model=PaymentConfirmOut, summary="결제 승인 (POS)")
async def confirm_payment(
    req: PaymentConfirmRequest,
    db: AsyncSession = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
):
    """
    POS에서 QR을 스캔하고 결제를 승인합니다.
    - Transaction 상태 → paid
    - CartSession 상태 → completed
    - ShoppingHistory 레코드 생성
    """
    try:
        result = await payment_service.confirm_payment(
            db=db,
            transaction_id=req.transaction_id,
            approval_number=req.approval_number,
        )
        return PaymentConfirmOut(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════
#  거래 내역 조회
# ═══════════════════════════════════════

@router.get("/transactions", response_model=list[TransactionOut], summary="거래 내역 목록")
async def list_transactions(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """사용자의 거래 내역을 최근순으로 반환합니다."""
    transactions = await payment_service.get_transactions(db, user_id, limit)
    return transactions


@router.get("/transactions/{transaction_id}", response_model=TransactionOut, summary="거래 상세")
async def get_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """특정 거래의 상세 정보를 반환합니다."""
    transaction = await payment_service.get_transaction_detail(db, transaction_id, user_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다.")
    return transaction


# ═══════════════════════════════════════
#  쇼핑 히스토리
# ═══════════════════════════════════════

@router.get("/history", response_model=list[ShoppingHistoryOut], summary="쇼핑 히스토리")
async def list_shopping_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """사용자의 쇼핑 히스토리를 최근순으로 반환합니다."""
    history = await payment_service.get_shopping_history(db, user_id, limit)
    return history
