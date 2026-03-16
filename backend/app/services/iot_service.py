"""
IoT 비즈니스 로직 서비스
- Beacon 위치 추정
- NFC 태그 조회 / 상품 연결
- ESL 업데이트 명령
"""
import math
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iot import Beacon, NfcTag
from app.models.product import Product, ProductPrice
from app.models.store import SpatialNode
from app.services.mqtt_service import mqtt_service

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════
#  Beacon 위치 추정
# ═══════════════════════════════════════

def _rssi_to_distance(rssi: int, tx_power: int = -59) -> float:
    """RSSI 값을 거리(m)로 변환 (Log-Distance Path Loss Model)"""
    if rssi == 0:
        return -1.0
    ratio = rssi / tx_power
    if ratio < 1.0:
        return ratio ** 10
    return 0.89976 * (ratio ** 7.7095) + 0.111


async def estimate_position_from_beacon(
    db: AsyncSession,
    store_id: UUID,
    beacon_uuid: str,
    major: int,
    minor: int,
    rssi: int,
) -> dict:
    """
    단일 비콘 신호로 위치 추정 (가장 가까운 비콘 기반).
    다중 비콘 삼각측위는 Step Z(하드웨어)에서 확장 예정.
    """
    # 비콘 조회
    result = await db.execute(
        select(Beacon).where(
            Beacon.store_id == store_id,
            Beacon.uuid == beacon_uuid,
            Beacon.major == major,
            Beacon.minor == minor,
            Beacon.is_active == True,
        )
    )
    beacon = result.scalars().first()

    if not beacon:
        return {
            "estimated_x": 0.0,
            "estimated_y": 0.0,
            "floor": 1,
            "nearest_node_id": None,
            "nearest_node_label": None,
            "confidence": 0.0,
        }

    # RSSI → 거리 변환
    distance = _rssi_to_distance(rssi, beacon.tx_power or -59)

    # 비콘 위치를 기반으로 추정 (단일 비콘이므로 비콘 좌표 자체가 추정치)
    est_x = float(beacon.x)
    est_y = float(beacon.y)
    floor = beacon.floor

    # 신뢰도 계산: RSSI가 강할수록 (가까울수록) 높음
    confidence = max(0.0, min(1.0, 1.0 - (distance / 20.0)))

    # 가장 가까운 공간 노드 찾기
    nodes_result = await db.execute(
        select(SpatialNode).where(
            SpatialNode.store_id == store_id,
            SpatialNode.floor == floor,
            SpatialNode.is_obstacle == False,
        )
    )
    nodes = nodes_result.scalars().all()

    nearest_node_id = None
    nearest_node_label = None
    min_dist = float("inf")

    for node in nodes:
        dx = float(node.x) - est_x
        dy = float(node.y) - est_y
        d = math.sqrt(dx * dx + dy * dy)
        if d < min_dist:
            min_dist = d
            nearest_node_id = node.node_id
            nearest_node_label = node.label

    return {
        "estimated_x": est_x,
        "estimated_y": est_y,
        "floor": floor,
        "nearest_node_id": nearest_node_id,
        "nearest_node_label": nearest_node_label,
        "confidence": round(confidence, 2),
    }


# ═══════════════════════════════════════
#  NFC 태그 처리
# ═══════════════════════════════════════

async def process_nfc_tag(
    db: AsyncSession,
    tag_uid: str,
    store_id: UUID,
) -> dict:
    """NFC 태그 태깅 시 연결된 상품 정보 반환"""
    # NFC 태그 조회
    result = await db.execute(
        select(NfcTag).where(
            NfcTag.tag_uid == tag_uid,
            NfcTag.store_id == store_id,
            NfcTag.is_active == True,
        )
    )
    tag = result.scalars().first()

    if not tag:
        return {
            "tag_uid": tag_uid,
            "product_id": None,
            "product_name": None,
            "regular_price": None,
            "sale_price": None,
            "location_desc": None,
            "action": "not_found",
        }

    # 연결된 상품 정보 조회
    product_name = None
    regular_price = None
    sale_price = None

    if tag.product_id:
        prod_result = await db.execute(
            select(Product).where(Product.product_id == tag.product_id)
        )
        product = prod_result.scalars().first()
        if product:
            product_name = product.product_name

        # 최신 가격 조회
        price_result = await db.execute(
            select(ProductPrice)
            .where(ProductPrice.product_id == tag.product_id)
            .order_by(ProductPrice.updated_at.desc())
            .limit(1)
        )
        price = price_result.scalars().first()
        if price:
            regular_price = int(price.regular_price)
            sale_price = int(price.sale_price) if price.sale_price else None

    # MQTT 응답 발행 (IoT 장치용)
    if tag.product_id and product_name:
        mqtt_service.publish_nfc_response(
            tag_uid=tag_uid,
            product_id=str(tag.product_id),
            product_name=product_name,
        )

    return {
        "tag_uid": tag_uid,
        "product_id": tag.product_id,
        "product_name": product_name,
        "regular_price": regular_price,
        "sale_price": sale_price,
        "location_desc": tag.location_desc,
        "action": "view_product" if tag.product_id else "info",
    }


# ═══════════════════════════════════════
#  ESL 업데이트
# ═══════════════════════════════════════

async def update_esl(
    mac_address: str,
    product_name: str,
    regular_price: int,
    sale_price: Optional[int] = None,
    store_name: str = "",
) -> dict:
    """ESL(전자가격표)에 MQTT를 통해 업데이트 명령 발행"""
    success = mqtt_service.publish_esl_update(
        mac_address=mac_address,
        product_name=product_name,
        regular_price=regular_price,
        sale_price=sale_price,
        store_name=store_name,
    )
    return {
        "mac_address": mac_address,
        "product_name": product_name,
        "regular_price": regular_price,
        "sale_price": sale_price,
        "last_updated": None,
        "mqtt_sent": success,
    }


# ═══════════════════════════════════════
#  Beacon / NFC 목록 조회
# ═══════════════════════════════════════

async def get_beacons(db: AsyncSession, store_id: UUID) -> list:
    """매장의 활성 비콘 목록"""
    result = await db.execute(
        select(Beacon).where(
            Beacon.store_id == store_id,
            Beacon.is_active == True,
        ).order_by(Beacon.beacon_id)
    )
    return result.scalars().all()


async def get_nfc_tags(db: AsyncSession, store_id: UUID) -> list:
    """매장의 활성 NFC 태그 목록"""
    result = await db.execute(
        select(NfcTag).where(
            NfcTag.store_id == store_id,
            NfcTag.is_active == True,
        ).order_by(NfcTag.nfc_tag_id)
    )
    return result.scalars().all()


async def get_iot_dashboard(db: AsyncSession, store_id: UUID) -> dict:
    """IoT 대시보드 통계"""
    # Beacon 통계
    total_beacons_r = await db.execute(
        select(func.count()).select_from(Beacon).where(Beacon.store_id == store_id)
    )
    total_beacons = total_beacons_r.scalar() or 0

    active_beacons_r = await db.execute(
        select(func.count()).select_from(Beacon).where(
            Beacon.store_id == store_id, Beacon.is_active == True
        )
    )
    active_beacons = active_beacons_r.scalar() or 0

    # NFC 통계
    total_nfc_r = await db.execute(
        select(func.count()).select_from(NfcTag).where(NfcTag.store_id == store_id)
    )
    total_nfc = total_nfc_r.scalar() or 0

    active_nfc_r = await db.execute(
        select(func.count()).select_from(NfcTag).where(
            NfcTag.store_id == store_id, NfcTag.is_active == True
        )
    )
    active_nfc = active_nfc_r.scalar() or 0

    return {
        "total_beacons": total_beacons,
        "active_beacons": active_beacons,
        "total_nfc_tags": total_nfc,
        "active_nfc_tags": active_nfc,
        "mqtt_connected": mqtt_service.connected,
    }
