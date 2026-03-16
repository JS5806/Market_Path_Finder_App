"""
경로 탐색 API 라우터
- 최적 쇼핑 경로 계산, 단일 최단 경로 조회
- 노드/엣지 CRUD (관리자용)
- 평면도 업로드
"""
import math
import os
import uuid as uuid_mod
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.common import ApiResponse
from app.schemas.route import (
    RouteOptimizeRequest,
    RouteFromCartRequest,
    RouteResultOut,
    ShortestPathRequest,
    ShortestPathOut,
)
from app.services import pathfinding_service
from app.models.user import CartSession, CartItem

router = APIRouter(prefix="/route", tags=["경로 탐색"])


@router.post("/optimize", response_model=ApiResponse[RouteResultOut])
async def optimize_route(
    data: RouteOptimizeRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    상품 ID 목록으로 최적 쇼핑 경로를 계산합니다.

    - Dijkstra 알고리즘으로 노드 간 최단 거리 계산
    - TSP 알고리즘으로 최적 방문 순서 결정
    - 입구 → 상품 경유지들 → 계산대 순서로 경로 반환
    """
    result = await pathfinding_service.optimize_route(
        db=db,
        store_id=data.store_id,
        product_ids=data.product_ids,
        start_node_id=data.start_node_id,
        end_node_id=data.end_node_id,
        avoid_congestion=data.avoid_congestion,
        user_id=user_id,
    )
    return ApiResponse(
        message="최적 경로가 계산되었습니다",
        data=result,
    )


@router.post("/optimize-cart", response_model=ApiResponse[RouteResultOut])
async def optimize_from_cart(
    data: RouteFromCartRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    현재 활성 장바구니의 상품들로 최적 쇼핑 경로를 계산합니다.

    장바구니에 담긴 모든 상품의 위치를 기반으로
    입구 → 상품들 → 계산대 최적 경로를 반환합니다.
    """
    # 활성 장바구니 조회
    cart_result = await db.execute(
        select(CartSession)
        .options(selectinload(CartSession.items))
        .where(
            CartSession.user_id == user_id,
            CartSession.status == "active",
        )
    )
    cart = cart_result.scalar_one_or_none()

    if not cart or not cart.items:
        return ApiResponse(
            success=False,
            message="활성 장바구니가 비어있습니다. 먼저 상품을 추가해주세요.",
            data=None,
        )

    product_ids = [item.product_id for item in cart.items]

    result = await pathfinding_service.optimize_route(
        db=db,
        store_id=data.store_id,
        product_ids=product_ids,
        start_node_id=data.start_node_id,
        end_node_id=data.end_node_id,
        avoid_congestion=data.avoid_congestion,
        user_id=user_id,
        session_id=cart.session_id,
    )
    return ApiResponse(
        message="장바구니 기반 최적 경로가 계산되었습니다",
        data=result,
    )


@router.post("/shortest-path", response_model=ApiResponse[ShortestPathOut])
async def get_shortest_path(
    data: ShortestPathRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    두 노드 간 최단 경로를 조회합니다.

    Dijkstra 알고리즘으로 두 지점 간 최단 거리와 경로를 반환합니다.
    인증 불필요 (매장 지도 탐색용)
    """
    result = await pathfinding_service.get_shortest_path(
        db=db,
        store_id=data.store_id,
        from_node_id=data.from_node_id,
        to_node_id=data.to_node_id,
    )
    return ApiResponse(data=result)


@router.get("/nodes", response_model=ApiResponse)
async def get_store_nodes(
    store_id: UUID = Query(..., description="매장 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    매장의 전체 공간 노드 목록을 조회합니다.

    프론트엔드 지도 렌더링용 - 인증 불필요
    """
    from app.models.store import SpatialNode
    result = await db.execute(
        select(SpatialNode)
        .where(SpatialNode.store_id == store_id)
        .order_by(SpatialNode.node_id)
    )
    nodes = result.scalars().all()
    nodes_data = [
        {
            "node_id": n.node_id,
            "x": float(n.x),
            "y": float(n.y),
            "floor": n.floor,
            "node_type": n.node_type,
            "label": n.label,
            "is_obstacle": n.is_obstacle,
        }
        for n in nodes
    ]
    return ApiResponse(data=nodes_data)


@router.get("/edges", response_model=ApiResponse)
async def get_store_edges(
    store_id: UUID = Query(..., description="매장 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    매장의 전체 간선(통로) 목록을 조회합니다.

    프론트엔드 지도 렌더링용 - 인증 불필요
    """
    from app.models.store import SpatialEdge
    result = await db.execute(
        select(SpatialEdge)
        .where(SpatialEdge.store_id == store_id)
        .order_by(SpatialEdge.edge_id)
    )
    edges = result.scalars().all()
    edges_data = [
        {
            "edge_id": e.edge_id,
            "from_node_id": e.from_node_id,
            "to_node_id": e.to_node_id,
            "distance": float(e.distance),
            "weight": float(e.weight) if e.weight else None,
            "is_bidirectional": e.is_bidirectional,
        }
        for e in edges
    ]
    return ApiResponse(data=edges_data)


# ════════════════════════════════════════════════════════
# 관리자용: 평면도 업로드 + 노드/엣지 CRUD
# ════════════════════════════════════════════════════════

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "floorplans")
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".dwg", ".dxf"}


@router.post("/floorplan/upload", response_model=ApiResponse)
async def upload_floorplan(
    store_id: str = Form(...),
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    매장 평면도 업로드 (관리자 전용)
    지원 형식: PNG, JPG, SVG, PDF, DWG, DXF
    - PNG/JPG/SVG: 이미지 그대로 배경으로 사용
    - PDF: 건축 도면 (첫 페이지 이미지 추출)
    - DWG/DXF: CAD 도면 (AutoCAD 매장 설계 파일)
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"지원하지 않는 파일 형식입니다. 지원: {', '.join(ALLOWED_EXTENSIONS)}")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{store_id}_{uuid_mod.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # 이미지 URL 반환 (프론트에서 배경으로 사용)
    url = f"/static/floorplans/{filename}"
    return ApiResponse(
        message="평면도가 업로드되었습니다",
        data={
            "filename": filename,
            "url": url,
            "size_bytes": len(content),
            "format": ext.lstrip("."),
            "store_id": store_id,
        },
    )


@router.post("/nodes", response_model=ApiResponse)
async def create_node(
    store_id: UUID = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    node_type: str = Form("waypoint"),
    label: str = Form(None),
    floor: int = Form(1),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    새 노드 추가 (관리자 전용)
    node_type: entrance, checkout, shelf, waypoint, aisle
    """
    from app.models.store import SpatialNode
    node = SpatialNode(
        store_id=store_id,
        x=x,
        y=y,
        node_type=node_type,
        label=label,
        floor=floor,
    )
    db.add(node)
    await db.flush()
    await db.refresh(node)
    return ApiResponse(
        message="노드가 추가되었습니다",
        data={
            "node_id": node.node_id,
            "x": float(node.x),
            "y": float(node.y),
            "node_type": node.node_type,
            "label": node.label,
            "floor": node.floor,
        },
    )


@router.put("/nodes/{node_id}", response_model=ApiResponse)
async def update_node(
    node_id: int,
    x: float = Form(None),
    y: float = Form(None),
    node_type: str = Form(None),
    label: str = Form(None),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """노드 정보 수정 (위치 이동, 타입/라벨 변경)"""
    from app.models.store import SpatialNode
    result = await db.execute(select(SpatialNode).where(SpatialNode.node_id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(404, "노드를 찾을 수 없습니다")

    if x is not None:
        node.x = x
    if y is not None:
        node.y = y
    if node_type is not None:
        node.node_type = node_type
    if label is not None:
        node.label = label
    await db.flush()
    return ApiResponse(
        message="노드가 수정되었습니다",
        data={
            "node_id": node.node_id,
            "x": float(node.x),
            "y": float(node.y),
            "node_type": node.node_type,
            "label": node.label,
        },
    )


@router.delete("/nodes/{node_id}", response_model=ApiResponse)
async def delete_node(
    node_id: int,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """노드 삭제 (연결된 엣지도 자동 삭제)"""
    from app.models.store import SpatialNode, SpatialEdge
    result = await db.execute(select(SpatialNode).where(SpatialNode.node_id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(404, "노드를 찾을 수 없습니다")

    # 연결된 엣지 먼저 삭제
    await db.execute(
        delete(SpatialEdge).where(
            (SpatialEdge.from_node_id == node_id) | (SpatialEdge.to_node_id == node_id)
        )
    )
    await db.delete(node)
    await db.flush()
    return ApiResponse(message="노드와 연결된 엣지가 삭제되었습니다")


@router.post("/edges", response_model=ApiResponse)
async def create_edge(
    store_id: UUID = Form(...),
    from_node_id: int = Form(...),
    to_node_id: int = Form(...),
    is_bidirectional: bool = Form(True),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    두 노드를 연결하는 엣지(경로) 추가
    거리(distance)는 좌표에서 자동 계산됩니다.
    """
    from app.models.store import SpatialNode, SpatialEdge

    # 두 노드 조회
    n1_res = await db.execute(select(SpatialNode).where(SpatialNode.node_id == from_node_id))
    n2_res = await db.execute(select(SpatialNode).where(SpatialNode.node_id == to_node_id))
    n1 = n1_res.scalar_one_or_none()
    n2 = n2_res.scalar_one_or_none()
    if not n1 or not n2:
        raise HTTPException(404, "연결할 노드를 찾을 수 없습니다")

    # 좌표로 거리 자동 계산
    dist = math.sqrt((float(n1.x) - float(n2.x)) ** 2 + (float(n1.y) - float(n2.y)) ** 2)

    edge = SpatialEdge(
        store_id=store_id,
        from_node_id=from_node_id,
        to_node_id=to_node_id,
        distance=round(dist, 2),
        is_bidirectional=is_bidirectional,
    )
    db.add(edge)
    await db.flush()
    await db.refresh(edge)
    return ApiResponse(
        message="엣지가 추가되었습니다",
        data={
            "edge_id": edge.edge_id,
            "from_node_id": edge.from_node_id,
            "to_node_id": edge.to_node_id,
            "distance": float(edge.distance),
            "is_bidirectional": edge.is_bidirectional,
        },
    )


@router.delete("/edges/{edge_id}", response_model=ApiResponse)
async def delete_edge(
    edge_id: int,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """엣지(경로 연결) 삭제"""
    from app.models.store import SpatialEdge
    result = await db.execute(select(SpatialEdge).where(SpatialEdge.edge_id == edge_id))
    edge = result.scalar_one_or_none()
    if not edge:
        raise HTTPException(404, "엣지를 찾을 수 없습니다")
    await db.delete(edge)
    await db.flush()
    return ApiResponse(message="엣지가 삭제되었습니다")
