"""
혼잡도 데이터 API 엔드포인트
- 구역별 실시간 혼잡도 조회
- 혼잡도 업데이트 (IoT 센서 / 관리자)
- 혼잡도 시뮬레이션 (데모용)
- 혼잡도 요약 통계
"""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.common import ApiResponse
from app.schemas.congestion import (
    CongestionOut,
    CongestionUpdateRequest,
    CongestionBulkUpdateRequest,
    CongestionUpdateOut,
    CongestionSummaryOut,
)
from app.services import congestion_service

router = APIRouter(prefix="/congestion", tags=["혼잡도"])


@router.get("/{store_id}", response_model=ApiResponse[list[CongestionOut]], summary="구역별 혼잡도 조회")
async def get_congestion(
    store_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    매장의 구역별 현재 혼잡도를 조회합니다.
    인증 불필요 (앱 진입 시 바로 확인 가능).
    density_level: 1(한산) ~ 5(매우 혼잡)
    """
    data = await congestion_service.get_congestion(db, store_id)
    return ApiResponse(data=data)


@router.put("/{store_id}", response_model=ApiResponse[CongestionUpdateOut], summary="구역 혼잡도 업데이트")
async def update_congestion(
    store_id: UUID,
    req: CongestionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
):
    """
    특정 구역의 혼잡도를 업데이트합니다.
    IoT 센서(비콘 밀도)나 관리자가 호출.
    """
    result = await congestion_service.update_congestion(
        db, store_id, req.zone_id, req.density_level,
    )
    return ApiResponse(message="혼잡도가 업데이트되었습니다", data=result)


@router.put("/{store_id}/bulk", response_model=ApiResponse[list[CongestionUpdateOut]], summary="일괄 혼잡도 업데이트")
async def bulk_update_congestion(
    store_id: UUID,
    req: CongestionBulkUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
):
    """
    여러 구역의 혼잡도를 한 번에 업데이트합니다.
    IoT 시스템에서 주기적으로 호출.
    """
    zone_data = [{"zone_id": z.zone_id, "density_level": z.density_level} for z in req.zones]
    results = await congestion_service.bulk_update_congestion(db, store_id, zone_data)
    return ApiResponse(message=f"{len(results)}개 구역 혼잡도 업데이트 완료", data=results)


@router.get("/{store_id}/summary", response_model=ApiResponse[CongestionSummaryOut], summary="혼잡도 요약")
async def congestion_summary(
    store_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    매장 혼잡도 요약 통계를 반환합니다.
    - 평균 혼잡도, 가장 혼잡/한산한 구역, 등급별 분포
    """
    data = await congestion_service.get_congestion_summary(db, store_id)
    return ApiResponse(data=data)


@router.post("/{store_id}/simulate", response_model=ApiResponse[list[CongestionUpdateOut]], summary="혼잡도 시뮬레이션")
async def simulate_congestion(
    store_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: UUID = Depends(get_current_user_id),
):
    """
    데모/발표용 혼잡도 시뮬레이션.
    모든 구역에 시간대 기반 랜덤 혼잡도를 할당합니다.
    """
    results = await congestion_service.simulate_congestion(db, store_id)
    return ApiResponse(
        message=f"{len(results)}개 구역에 시뮬레이션 혼잡도 적용",
        data=results,
    )
