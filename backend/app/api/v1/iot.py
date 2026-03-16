"""
IoT API 엔드포인트 (Beacon, NFC, ESL)
"""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.iot import (
    BeaconOut, BeaconSignalRequest, BeaconPositionOut,
    NfcTagOut, NfcTagRequest, NfcTagResponse,
    EslUpdateRequest, EslStatusOut,
    IotDashboardOut,
)
from app.services import iot_service

router = APIRouter(prefix="/iot", tags=["IoT 장치"])


# ═══════════════════════════════════════
#  Beacon 엔드포인트
# ═══════════════════════════════════════

@router.get("/beacons/{store_id}", response_model=list[BeaconOut], summary="매장 비콘 목록")
async def list_beacons(
    store_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
):
    """매장에 설치된 활성 비콘 목록을 반환합니다."""
    beacons = await iot_service.get_beacons(db, store_id)
    return beacons


@router.post("/beacon/signal", response_model=BeaconPositionOut, summary="비콘 신호 → 위치 추정")
async def report_beacon_signal(
    req: BeaconSignalRequest,
    db: AsyncSession = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
):
    """
    모바일 앱이 수신한 BLE 비콘 신호를 보고하면,
    RSSI 기반으로 매장 내 위치를 추정합니다.
    """
    result = await iot_service.estimate_position_from_beacon(
        db=db,
        store_id=req.store_id,
        beacon_uuid=req.beacon_uuid,
        major=req.major,
        minor=req.minor,
        rssi=req.rssi,
    )
    return BeaconPositionOut(**result)


# ═══════════════════════════════════════
#  NFC 엔드포인트
# ═══════════════════════════════════════

@router.get("/nfc-tags/{store_id}", response_model=list[NfcTagOut], summary="매장 NFC 태그 목록")
async def list_nfc_tags(
    store_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
):
    """매장에 등록된 활성 NFC 태그 목록을 반환합니다."""
    tags = await iot_service.get_nfc_tags(db, store_id)
    return tags


@router.post("/nfc/tag", response_model=NfcTagResponse, summary="NFC 태깅 처리")
async def process_nfc_tagging(
    req: NfcTagRequest,
    db: AsyncSession = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
):
    """
    사용자가 NFC 태그를 태깅하면 연결된 상품 정보를 반환합니다.
    동시에 MQTT로 IoT 장치에 응답을 발행합니다.
    """
    result = await iot_service.process_nfc_tag(
        db=db,
        tag_uid=req.tag_uid,
        store_id=req.store_id,
    )
    return NfcTagResponse(**result)


# ═══════════════════════════════════════
#  ESL (전자가격표) 엔드포인트
# ═══════════════════════════════════════

@router.post("/esl/update", response_model=EslStatusOut, summary="ESL 가격표 업데이트")
async def update_esl_display(
    req: EslUpdateRequest,
    _user_id: UUID = Depends(get_current_user_id),
):
    """
    ESL(전자가격표)에 MQTT를 통해 상품/가격 업데이트 명령을 보냅니다.
    실제 E-Ink 디스플레이는 ESP32가 MQTT 메시지를 수신하여 처리합니다.
    """
    result = await iot_service.update_esl(
        mac_address=req.mac_address,
        product_name=req.product_name,
        regular_price=req.regular_price,
        sale_price=req.sale_price,
        store_name=req.store_name,
    )
    return EslStatusOut(**result)


# ═══════════════════════════════════════
#  IoT 대시보드
# ═══════════════════════════════════════

@router.get("/dashboard/{store_id}", response_model=IotDashboardOut, summary="IoT 장치 현황")
async def iot_dashboard(
    store_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
):
    """매장의 IoT 장치(비콘, NFC, MQTT) 현황을 요약합니다."""
    result = await iot_service.get_iot_dashboard(db, store_id)
    return IotDashboardOut(**result)
