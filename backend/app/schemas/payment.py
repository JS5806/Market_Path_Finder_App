"""
결제 및 거래 관련 Pydantic 스키마
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ═══════════════════════════════════════
#  QR 결제 생성
# ═══════════════════════════════════════

class QrPaymentRequest(BaseModel):
    """QR 결제 생성 요청"""
    session_id: UUID = Field(..., description="장바구니 세션 ID")
    store_id: UUID = Field(..., description="매장 ID")


class QrPaymentOut(BaseModel):
    """QR 결제 정보 (생성 결과)"""
    transaction_id: UUID
    qr_payload: str = Field(..., description="QR 코드에 인코딩될 결제 데이터 (JSON 문자열)")
    total_amount: int = Field(..., description="총 결제 금액")
    item_count: int = Field(..., description="상품 수량")
    status: str = Field("pending", description="결제 상태")
    created_at: datetime


# ═══════════════════════════════════════
#  결제 승인 (POS에서 호출)
# ═══════════════════════════════════════

class PaymentConfirmRequest(BaseModel):
    """결제 승인 요청 (POS 시스템에서 QR 스캔 후)"""
    transaction_id: UUID = Field(..., description="거래 ID")
    approval_number: str = Field(..., description="POS 승인 번호")


class PaymentConfirmOut(BaseModel):
    """결제 승인 결과"""
    transaction_id: UUID
    status: str
    approval_number: str
    total_amount: int
    paid_at: Optional[datetime] = None


# ═══════════════════════════════════════
#  거래 내역 조회
# ═══════════════════════════════════════

class TransactionOut(BaseModel):
    """거래 내역"""
    transaction_id: UUID
    store_id: UUID
    session_id: UUID
    total_amount: int
    payment_method: str
    approval_number: Optional[str] = None
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ShoppingHistoryOut(BaseModel):
    """쇼핑 히스토리"""
    history_id: int
    store_id: UUID
    session_id: Optional[UUID] = None
    total_amount: int
    item_count: int
    shopped_at: datetime

    class Config:
        from_attributes = True
