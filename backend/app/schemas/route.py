"""
경로 탐색 관련 Pydantic 스키마
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ── 경로 최적화 요청 ──
class RouteOptimizeRequest(BaseModel):
    store_id: UUID = Field(..., description="매장 ID")
    product_ids: list[UUID] = Field(..., min_length=1, description="장바구니 상품 ID 목록")
    start_node_id: Optional[int] = Field(None, description="시작 노드 (기본: 입구)")
    end_node_id: Optional[int] = Field(None, description="종료 노드 (기본: 계산대)")
    avoid_congestion: bool = Field(False, description="혼잡 구역 회피 여부")


# ── 경로 최적화 (장바구니 기반) 요청 ──
class RouteFromCartRequest(BaseModel):
    store_id: UUID = Field(..., description="매장 ID")
    start_node_id: Optional[int] = Field(None, description="시작 노드 (기본: 입구)")
    end_node_id: Optional[int] = Field(None, description="종료 노드 (기본: 계산대)")
    avoid_congestion: bool = Field(False, description="혼잡 구역 회피 여부")


# ── 경유 노드 정보 ──
class RouteStopOut(BaseModel):
    order: int = Field(..., description="방문 순서 (0부터)")
    node_id: int
    x: float
    y: float
    label: Optional[str] = None
    node_type: str
    product_ids: list[UUID] = Field(default_factory=list, description="이 노드에서 픽업할 상품들")
    product_names: list[str] = Field(default_factory=list, description="상품명 목록")


# ── 구간별 경로 (노드→노드 세부 경로) ──
class RouteSegmentOut(BaseModel):
    from_node_id: int
    to_node_id: int
    path_node_ids: list[int] = Field(..., description="Dijkstra 최단 경로 노드 순서")
    distance: float


# ── 전체 경로 결과 ──
class RouteResultOut(BaseModel):
    route_id: Optional[int] = None
    store_id: UUID
    algorithm: str = "dijkstra+tsp"
    visit_order: list[RouteStopOut] = Field(..., description="최적 방문 순서")
    segments: list[RouteSegmentOut] = Field(default_factory=list, description="구간별 세부 경로")
    total_distance: float = Field(..., description="총 이동 거리 (m)")
    estimated_time_min: float = Field(..., description="예상 소요 시간 (분)")
    computed_at: datetime


# ── 단일 경로 조회 (두 노드 사이 최단 경로) ──
class ShortestPathRequest(BaseModel):
    store_id: UUID
    from_node_id: int
    to_node_id: int


class ShortestPathOut(BaseModel):
    from_node_id: int
    to_node_id: int
    path: list[int] = Field(..., description="최단 경로 노드 ID 순서")
    distance: float
    path_details: list[dict] = Field(default_factory=list, description="경로 상 각 노드 좌표")
