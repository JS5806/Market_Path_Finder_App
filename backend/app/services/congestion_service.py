"""
혼잡도 데이터 서비스
- 구역별 혼잡도 조회/등록/업데이트
- Beacon 기반 자동 혼잡도 추정 (시뮬레이션)
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import CongestionData, CategoryZone

logger = logging.getLogger(__name__)


async def get_congestion(
    db: AsyncSession,
    store_id: UUID,
) -> list[dict]:
    """
    매장의 현재 구역별 혼잡도 데이터를 반환합니다.
    CategoryZone 이름과 함께 반환.
    """
    result = await db.execute(
        select(CongestionData, CategoryZone)
        .join(CategoryZone, CongestionData.zone_id == CategoryZone.zone_id)
        .where(CongestionData.store_id == store_id)
        .order_by(CongestionData.zone_id)
    )
    rows = result.all()

    return [
        {
            "congestion_id": c.congestion_id,
            "zone_id": c.zone_id,
            "zone_name": z.zone_name,
            "category_code": z.category_code,
            "density_level": c.density_level,
            "measured_at": c.measured_at,
        }
        for c, z in rows
    ]


async def update_congestion(
    db: AsyncSession,
    store_id: UUID,
    zone_id: int,
    density_level: int,
) -> dict:
    """
    특정 구역의 혼잡도를 업데이트합니다.
    기존 데이터가 있으면 업데이트, 없으면 신규 생성.
    density_level: 1(한산) ~ 5(매우 혼잡)
    """
    if density_level < 1 or density_level > 5:
        raise ValueError("혼잡도는 1~5 범위여야 합니다.")

    # 기존 데이터 확인
    existing = await db.execute(
        select(CongestionData).where(
            CongestionData.store_id == store_id,
            CongestionData.zone_id == zone_id,
        )
    )
    record = existing.scalars().first()
    now = datetime.now(timezone.utc)

    if record:
        record.density_level = density_level
        record.measured_at = now
    else:
        record = CongestionData(
            store_id=store_id,
            zone_id=zone_id,
            density_level=density_level,
            measured_at=now,
        )
        db.add(record)

    await db.flush()
    await db.refresh(record)

    # zone 이름 가져오기
    zone_r = await db.execute(
        select(CategoryZone).where(CategoryZone.zone_id == zone_id)
    )
    zone = zone_r.scalars().first()

    return {
        "congestion_id": record.congestion_id,
        "zone_id": zone_id,
        "zone_name": zone.zone_name if zone else None,
        "density_level": density_level,
        "measured_at": now,
        "status": "updated",
    }


async def bulk_update_congestion(
    db: AsyncSession,
    store_id: UUID,
    zone_data: list[dict],
) -> list[dict]:
    """
    여러 구역의 혼잡도를 한 번에 업데이트합니다.
    zone_data: [{"zone_id": int, "density_level": int}, ...]
    """
    results = []
    for item in zone_data:
        r = await update_congestion(
            db, store_id,
            zone_id=item["zone_id"],
            density_level=item["density_level"],
        )
        results.append(r)
    return results


async def get_congestion_summary(
    db: AsyncSession,
    store_id: UUID,
) -> dict:
    """
    매장 혼잡도 요약 통계를 반환합니다.
    - 평균 혼잡도
    - 가장 혼잡한/한산한 구역
    - 구역별 분포
    """
    data = await get_congestion(db, store_id)

    if not data:
        return {
            "store_id": store_id,
            "total_zones": 0,
            "avg_density": 0.0,
            "most_congested": None,
            "least_congested": None,
            "distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        }

    densities = [d["density_level"] for d in data]
    avg = sum(densities) / len(densities)

    # 분포
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for d in densities:
        dist[d] = dist.get(d, 0) + 1

    most = max(data, key=lambda x: x["density_level"])
    least = min(data, key=lambda x: x["density_level"])

    return {
        "store_id": store_id,
        "total_zones": len(data),
        "avg_density": round(avg, 1),
        "most_congested": {
            "zone_name": most["zone_name"],
            "density_level": most["density_level"],
        },
        "least_congested": {
            "zone_name": least["zone_name"],
            "density_level": least["density_level"],
        },
        "distribution": dist,
    }


async def simulate_congestion(
    db: AsyncSession,
    store_id: UUID,
) -> list[dict]:
    """
    혼잡도 시뮬레이션 (데모/발표용).
    모든 구역에 랜덤 혼잡도를 할당합니다.
    """
    import random

    # 매장의 모든 구역 조회
    zone_result = await db.execute(
        select(CategoryZone).where(CategoryZone.store_id == store_id)
    )
    zones = zone_result.scalars().all()

    if not zones:
        return []

    results = []
    now = datetime.now(timezone.utc)

    for zone in zones:
        # 시간대에 따른 가중치 (낮 시간에 더 혼잡)
        hour = now.hour
        base = 2 if 10 <= hour <= 18 else 1
        density = min(5, max(1, base + random.randint(-1, 2)))

        r = await update_congestion(db, store_id, zone.zone_id, density)
        results.append(r)

    return results
