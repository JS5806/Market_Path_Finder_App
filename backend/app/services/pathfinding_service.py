"""
경로 탐색 서비스 - Dijkstra 최단 경로 + TSP 최적 방문 순서
마트 내 상품 위치 기반 최적 쇼핑 경로를 계산합니다.
"""
import heapq
from itertools import permutations
from decimal import Decimal
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.store import SpatialNode, SpatialEdge, CongestionData, CategoryZone
from app.models.product import ProductLocation, Product
from app.models.iot import RouteResult


# ── 그래프 구축 ──

async def build_graph(
    db: AsyncSession,
    store_id: UUID,
    avoid_congestion: bool = False,
) -> tuple[dict, dict]:
    """
    매장의 공간 그래프를 구축합니다.

    Returns:
        graph: {node_id: [(neighbor_id, distance), ...]}
        nodes_info: {node_id: {"x": float, "y": float, "label": str, "node_type": str}}
    """
    # 노드 로드
    node_result = await db.execute(
        select(SpatialNode).where(
            SpatialNode.store_id == store_id,
            SpatialNode.is_obstacle == False,
        )
    )
    nodes = node_result.scalars().all()
    if not nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="매장의 공간 노드 데이터가 없습니다",
        )

    nodes_info = {}
    for n in nodes:
        nodes_info[n.node_id] = {
            "x": float(n.x),
            "y": float(n.y),
            "label": n.label,
            "node_type": n.node_type,
            "floor": n.floor,
        }

    # 간선 로드
    edge_result = await db.execute(
        select(SpatialEdge).where(SpatialEdge.store_id == store_id)
    )
    edges = edge_result.scalars().all()

    # 혼잡도 가중치 로드 (선택적)
    congestion_map = {}
    if avoid_congestion:
        cong_result = await db.execute(
            select(CongestionData)
            .join(CategoryZone, CongestionData.zone_id == CategoryZone.zone_id)
            .where(CongestionData.store_id == store_id)
        )
        for c in cong_result.scalars().all():
            zone_result = await db.execute(
                select(CategoryZone).where(CategoryZone.zone_id == c.zone_id)
            )
            zone = zone_result.scalar_one_or_none()
            if zone and zone.node_id:
                congestion_map[zone.node_id] = int(c.density_level)

    # 인접 리스트 구축
    graph: dict[int, list[tuple[int, float]]] = {nid: [] for nid in nodes_info}

    for edge in edges:
        from_id = edge.from_node_id
        to_id = edge.to_node_id
        dist = float(edge.distance)

        # 혼잡도 반영: weight가 있으면 그것 사용, 아니면 distance 사용
        weight = float(edge.weight) if edge.weight else dist

        # 혼잡도 회피: 혼잡한 노드로의 이동에 페널티 부여
        if avoid_congestion:
            if to_id in congestion_map:
                penalty = congestion_map[to_id] * 0.3  # 혼잡도 1당 30% 가중
                weight *= (1 + penalty)
            if from_id in congestion_map:
                penalty = congestion_map[from_id] * 0.3
                weight *= (1 + penalty)

        if from_id in graph and to_id in graph:
            graph[from_id].append((to_id, weight))
            if edge.is_bidirectional:
                graph[to_id].append((from_id, weight))

    return graph, nodes_info


# ── Dijkstra 최단 경로 ──

def dijkstra(
    graph: dict[int, list[tuple[int, float]]],
    start: int,
    end: int,
) -> tuple[list[int], float]:
    """
    Dijkstra 알고리즘으로 두 노드 간 최단 경로를 찾습니다.

    Returns:
        path: 최단 경로 노드 ID 리스트 (start → end)
        distance: 총 거리
    """
    if start not in graph or end not in graph:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"노드 {start} 또는 {end}가 그래프에 존재하지 않습니다",
        )

    # 거리 테이블
    dist = {node: float("inf") for node in graph}
    dist[start] = 0
    prev = {node: None for node in graph}

    # 우선순위 큐: (거리, 노드)
    pq = [(0, start)]
    visited = set()

    while pq:
        current_dist, current = heapq.heappop(pq)

        if current in visited:
            continue
        visited.add(current)

        if current == end:
            break

        for neighbor, weight in graph[current]:
            if neighbor in visited:
                continue
            new_dist = current_dist + weight
            if new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                prev[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))

    # 경로 복원
    if dist[end] == float("inf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"노드 {start}에서 {end}까지 도달 가능한 경로가 없습니다",
        )

    path = []
    current = end
    while current is not None:
        path.append(current)
        current = prev[current]
    path.reverse()

    return path, dist[end]


def dijkstra_all_pairs(
    graph: dict[int, list[tuple[int, float]]],
    target_nodes: list[int],
) -> dict[tuple[int, int], tuple[list[int], float]]:
    """
    대상 노드들 간의 모든 쌍 최단 경로를 계산합니다.

    Returns:
        {(from_id, to_id): (path, distance)}
    """
    result = {}
    for src in target_nodes:
        for dst in target_nodes:
            if src != dst:
                try:
                    path, dist = dijkstra(graph, src, dst)
                    result[(src, dst)] = (path, dist)
                except HTTPException:
                    result[(src, dst)] = ([], float("inf"))
    return result


# ── TSP 최적 방문 순서 ──

def solve_tsp(
    target_nodes: list[int],
    start_node: int,
    end_node: int,
    pair_distances: dict[tuple[int, int], tuple[list[int], float]],
) -> tuple[list[int], float]:
    """
    TSP (Traveling Salesman Problem)를 풀어 최적 방문 순서를 결정합니다.

    - 상품 경유지가 8개 이하: 브루트포스 (정확 해)
    - 9개 이상: Nearest Neighbor 휴리스틱 (근사 해)

    Returns:
        visit_order: [start_node, ...경유지..., end_node]
        total_distance: 총 이동 거리
    """
    # 경유지 = 시작/종료 제외한 상품 노드들
    waypoints = [n for n in target_nodes if n != start_node and n != end_node]

    if not waypoints:
        # 경유지 없이 시작→종료 직행
        if (start_node, end_node) in pair_distances:
            _, dist = pair_distances[(start_node, end_node)]
            return [start_node, end_node], dist
        return [start_node, end_node], 0.0

    # 중복 노드 제거 (같은 코너에 있는 상품들)
    waypoints = list(set(waypoints))

    if len(waypoints) <= 8:
        # 브루트포스: 모든 순열 탐색
        return _tsp_bruteforce(waypoints, start_node, end_node, pair_distances)
    else:
        # Nearest Neighbor 휴리스틱
        return _tsp_nearest_neighbor(waypoints, start_node, end_node, pair_distances)


def _get_pair_distance(
    pair_distances: dict[tuple[int, int], tuple[list[int], float]],
    a: int,
    b: int,
) -> float:
    """두 노드 간 거리를 조회합니다."""
    if a == b:
        return 0.0
    if (a, b) in pair_distances:
        return pair_distances[(a, b)][1]
    return float("inf")


def _tsp_bruteforce(
    waypoints: list[int],
    start: int,
    end: int,
    pair_distances: dict[tuple[int, int], tuple[list[int], float]],
) -> tuple[list[int], float]:
    """브루트포스 TSP (경유지 8개 이하)"""
    best_order = None
    best_dist = float("inf")

    for perm in permutations(waypoints):
        # 총 거리 = start→perm[0] + perm[0]→perm[1] + ... + perm[-1]→end
        total = 0.0
        route = [start] + list(perm) + [end]

        for i in range(len(route) - 1):
            d = _get_pair_distance(pair_distances, route[i], route[i + 1])
            total += d
            if total >= best_dist:
                break  # 가지치기

        if total < best_dist:
            best_dist = total
            best_order = route

    return best_order or [start, end], best_dist


def _tsp_nearest_neighbor(
    waypoints: list[int],
    start: int,
    end: int,
    pair_distances: dict[tuple[int, int], tuple[list[int], float]],
) -> tuple[list[int], float]:
    """Nearest Neighbor 휴리스틱 TSP (경유지 9개 이상)"""
    remaining = set(waypoints)
    current = start
    route = [start]
    total_dist = 0.0

    while remaining:
        nearest = None
        nearest_dist = float("inf")

        for candidate in remaining:
            d = _get_pair_distance(pair_distances, current, candidate)
            if d < nearest_dist:
                nearest_dist = d
                nearest = candidate

        if nearest is None:
            break

        route.append(nearest)
        total_dist += nearest_dist
        current = nearest
        remaining.remove(nearest)

    # 마지막 경유지 → 종료 노드
    total_dist += _get_pair_distance(pair_distances, current, end)
    route.append(end)

    return route, total_dist


# ── 상품 위치 조회 ──

async def get_product_node_map(
    db: AsyncSession,
    store_id: UUID,
    product_ids: list[UUID],
) -> dict[int, list[dict]]:
    """
    상품들의 매장 내 노드 위치를 조회합니다.

    Returns:
        {node_id: [{"product_id": UUID, "product_name": str}, ...]}
    """
    result = await db.execute(
        select(ProductLocation, Product)
        .join(Product, ProductLocation.product_id == Product.product_id)
        .where(
            ProductLocation.store_id == store_id,
            ProductLocation.product_id.in_(product_ids),
            ProductLocation.node_id.isnot(None),
        )
    )
    rows = result.all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 매장에서 상품 위치 정보를 찾을 수 없습니다",
        )

    node_product_map: dict[int, list[dict]] = {}
    for loc, product in rows:
        nid = loc.node_id
        if nid not in node_product_map:
            node_product_map[nid] = []
        node_product_map[nid].append({
            "product_id": product.product_id,
            "product_name": product.product_name,
        })

    return node_product_map


# ── 시작/종료 노드 자동 탐색 ──

async def find_special_node(
    db: AsyncSession,
    store_id: UUID,
    node_type: str,
) -> Optional[int]:
    """특정 타입의 노드를 찾습니다 (entrance, checkout 등)"""
    result = await db.execute(
        select(SpatialNode).where(
            SpatialNode.store_id == store_id,
            SpatialNode.node_type == node_type,
        ).limit(1)
    )
    node = result.scalar_one_or_none()
    return node.node_id if node else None


# ── 메인 경로 최적화 함수 ──

async def optimize_route(
    db: AsyncSession,
    store_id: UUID,
    product_ids: list[UUID],
    start_node_id: Optional[int] = None,
    end_node_id: Optional[int] = None,
    avoid_congestion: bool = False,
    user_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
) -> dict:
    """
    장바구니 상품들의 최적 쇼핑 경로를 계산합니다.

    1. 상품 → 노드 매핑
    2. 그래프 구축
    3. 시작/종료 노드 결정
    4. 모든 쌍 최단 경로 (Dijkstra)
    5. TSP로 최적 방문 순서 결정
    6. 결과 조합 및 DB 저장
    """
    # 1. 상품 → 노드 매핑
    node_product_map = await get_product_node_map(db, store_id, product_ids)

    # 2. 그래프 구축
    graph, nodes_info = await build_graph(db, store_id, avoid_congestion)

    # 3. 시작/종료 노드 결정
    if start_node_id is None:
        start_node_id = await find_special_node(db, store_id, "entrance")
        if start_node_id is None:
            raise HTTPException(status_code=400, detail="매장 입구 노드를 찾을 수 없습니다")

    if end_node_id is None:
        end_node_id = await find_special_node(db, store_id, "checkout")
        if end_node_id is None:
            end_node_id = start_node_id  # 계산대 없으면 입구로 복귀

    # 4. 대상 노드 목록 (시작 + 상품 노드들 + 종료)
    product_nodes = list(node_product_map.keys())
    all_target_nodes = list(set([start_node_id] + product_nodes + [end_node_id]))

    # 5. 모든 쌍 최단 경로
    pair_distances = dijkstra_all_pairs(graph, all_target_nodes)

    # 6. TSP 최적 방문 순서
    visit_order, total_distance = solve_tsp(
        product_nodes, start_node_id, end_node_id, pair_distances
    )

    # 7. 결과 조합
    visit_stops = []
    segments = []

    for idx, node_id in enumerate(visit_order):
        info = nodes_info.get(node_id, {})
        products_at_node = node_product_map.get(node_id, [])

        visit_stops.append({
            "order": idx,
            "node_id": node_id,
            "x": info.get("x", 0),
            "y": info.get("y", 0),
            "label": info.get("label"),
            "node_type": info.get("node_type", "waypoint"),
            "product_ids": [p["product_id"] for p in products_at_node],
            "product_names": [p["product_name"] for p in products_at_node],
        })

        # 구간별 세부 경로
        if idx > 0:
            prev_node = visit_order[idx - 1]
            if (prev_node, node_id) in pair_distances:
                seg_path, seg_dist = pair_distances[(prev_node, node_id)]
                segments.append({
                    "from_node_id": prev_node,
                    "to_node_id": node_id,
                    "path_node_ids": seg_path,
                    "distance": seg_dist,
                })

    # 예상 소요 시간 (평균 보행 속도 1.2m/s = 72m/min)
    estimated_time = total_distance / 72.0 if total_distance > 0 else 0
    # 상품 픽업 시간 추가 (상품당 약 15초)
    pickup_count = sum(len(node_product_map.get(n, [])) for n in product_nodes)
    estimated_time += pickup_count * 0.25  # 15초 = 0.25분

    computed_at = datetime.now(timezone.utc)

    # 8. DB에 결과 저장
    visit_order_json = [
        {
            "node_id": stop["node_id"],
            "x": stop["x"],
            "y": stop["y"],
            "label": stop["label"],
            "product_ids": [str(pid) for pid in stop["product_ids"]],
        }
        for stop in visit_stops
    ]

    route_record = RouteResult(
        user_id=user_id,
        session_id=session_id,
        store_id=store_id,
        visit_order=visit_order_json,
        total_distance=Decimal(str(round(total_distance, 2))),
        algorithm="dijkstra+tsp",
        computed_at=computed_at,
    )

    if user_id:
        db.add(route_record)
        await db.flush()
        await db.refresh(route_record)

    return {
        "route_id": route_record.route_id if user_id else None,
        "store_id": store_id,
        "algorithm": "dijkstra+tsp",
        "visit_order": visit_stops,
        "segments": segments,
        "total_distance": round(total_distance, 2),
        "estimated_time_min": round(estimated_time, 1),
        "computed_at": computed_at,
    }


# ── 단일 최단 경로 조회 ──

async def get_shortest_path(
    db: AsyncSession,
    store_id: UUID,
    from_node_id: int,
    to_node_id: int,
) -> dict:
    """두 노드 간 최단 경로를 반환합니다."""
    graph, nodes_info = await build_graph(db, store_id)
    path, distance = dijkstra(graph, from_node_id, to_node_id)

    path_details = []
    for nid in path:
        info = nodes_info.get(nid, {})
        path_details.append({
            "node_id": nid,
            "x": info.get("x", 0),
            "y": info.get("y", 0),
            "label": info.get("label"),
            "node_type": info.get("node_type"),
        })

    return {
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "path": path,
        "distance": round(distance, 2),
        "path_details": path_details,
    }
