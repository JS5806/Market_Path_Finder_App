"""
혼잡도 데이터 Pydantic 스키마
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class CongestionOut(BaseModel):
    """구역별 혼잡도 응답"""
    congestion_id: int
    zone_id: int
    zone_name: str
    category_code: str
    density_level: int = Field(..., ge=1, le=5, description="1=한산 ~ 5=매우혼잡")
    measured_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CongestionUpdateRequest(BaseModel):
    """단일 구역 혼잡도 업데이트 요청"""
    zone_id: int = Field(..., description="구역 ID")
    density_level: int = Field(..., ge=1, le=5, description="1=한산 ~ 5=매우혼잡")


class CongestionBulkUpdateRequest(BaseModel):
    """다중 구역 혼잡도 일괄 업데이트 요청"""
    store_id: UUID
    zones: list[CongestionUpdateRequest] = Field(..., min_length=1)


class CongestionUpdateOut(BaseModel):
    """혼잡도 업데이트 결과"""
    congestion_id: int
    zone_id: int
    zone_name: Optional[str] = None
    density_level: int
    measured_at: datetime
    status: str = "updated"


class CongestionSummaryOut(BaseModel):
    """혼잡도 요약 통계"""
    store_id: UUID
    total_zones: int
    avg_density: float
    most_congested: Optional[dict] = None
    least_congested: Optional[dict] = None
    distribution: dict = Field(default_factory=dict, description="{1: n, 2: n, ...}")
