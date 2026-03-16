"""
IoT 장치 관련 Pydantic 스키마 (Beacon, NFC, ESL)
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ═══════════════════════════════════════
#  Beacon (BLE 비콘)
# ═══════════════════════════════════════

class BeaconOut(BaseModel):
    beacon_id: int
    store_id: UUID
    uuid: str
    major: int
    minor: int
    x: float
    y: float
    floor: int
    tx_power: int
    label: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class BeaconSignalRequest(BaseModel):
    """모바일 앱에서 수신한 비콘 신호 보고"""
    beacon_uuid: str = Field(..., description="비콘 UUID")
    major: int = Field(..., description="major 값")
    minor: int = Field(..., description="minor 값")
    rssi: int = Field(..., description="수신 신호 세기 (dBm)")
    store_id: UUID = Field(..., description="매장 ID")


class BeaconPositionOut(BaseModel):
    """비콘 신호 기반 위치 추정 결과"""
    estimated_x: float
    estimated_y: float
    floor: int
    nearest_node_id: Optional[int] = None
    nearest_node_label: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0, description="위치 추정 신뢰도 (0~1)")


# ═══════════════════════════════════════
#  NFC 태그
# ═══════════════════════════════════════

class NfcTagOut(BaseModel):
    nfc_tag_id: int
    tag_uid: str
    store_id: UUID
    product_id: Optional[UUID] = None
    location_desc: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class NfcTagRequest(BaseModel):
    """NFC 태그 태깅 이벤트"""
    tag_uid: str = Field(..., description="NFC 태그 UID")
    store_id: UUID = Field(..., description="매장 ID")


class NfcTagResponse(BaseModel):
    """NFC 태깅 결과 - 연결된 상품 정보"""
    tag_uid: str
    product_id: Optional[UUID] = None
    product_name: Optional[str] = None
    regular_price: Optional[int] = None
    sale_price: Optional[int] = None
    location_desc: Optional[str] = None
    action: str = Field("view_product", description="앱에서 수행할 동작")


# ═══════════════════════════════════════
#  ESL (전자가격표)
# ═══════════════════════════════════════

class EslUpdateRequest(BaseModel):
    """ESL 업데이트 요청"""
    mac_address: str = Field(..., description="ESL 장치 MAC 주소")
    product_name: str = Field(..., description="상품명")
    regular_price: int = Field(..., ge=0, description="정가")
    sale_price: Optional[int] = Field(None, ge=0, description="할인가")
    store_name: str = Field("", description="매장명")


class EslStatusOut(BaseModel):
    """ESL 장치 상태"""
    mac_address: str
    product_name: str
    regular_price: int
    sale_price: Optional[int] = None
    last_updated: Optional[datetime] = None
    mqtt_sent: bool = False


# ═══════════════════════════════════════
#  IoT 대시보드 요약
# ═══════════════════════════════════════

class IotDashboardOut(BaseModel):
    """IoT 장치 현황 대시보드"""
    total_beacons: int
    active_beacons: int
    total_nfc_tags: int
    active_nfc_tags: int
    mqtt_connected: bool
