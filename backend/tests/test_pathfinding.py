"""
Step 10 — 경로 탐색 알고리즘 단위 테스트
Dijkstra 최단 경로 + TSP 방문 순서 최적화
(순수 함수 테스트: DB 불필요)
"""
import pytest
from app.services.pathfinding_service import (
    dijkstra,
    dijkstra_all_pairs,
    solve_tsp,
    _tsp_bruteforce,
    _tsp_nearest_neighbor,
    _get_pair_distance,
)


class TestDijkstra:
    """Dijkstra 최단 경로 알고리즘 테스트"""

    def test_direct_neighbor(self, sample_graph):
        """인접 노드 직접 이동"""
        path, dist = dijkstra(sample_graph, 1, 2)
        assert path == [1, 2]
        assert dist == 5.0

    def test_shortest_path_entrance_to_checkout(self, sample_graph):
        """입구(1) → 계산대(10) 최단 경로"""
        path, dist = dijkstra(sample_graph, 1, 10)
        # 1→2→3→4→7→10 (5+4+3+4+3=19) vs 1→2→5→6→9→10 (5+3+4+3+4=19) vs 1→2→3→6→7→10 (5+4+3+4+3=19)
        assert path[0] == 1
        assert path[-1] == 10
        assert dist == 19.0

    def test_same_node(self, sample_graph):
        """시작과 끝이 같은 노드"""
        path, dist = dijkstra(sample_graph, 5, 5)
        assert path == [5]
        assert dist == 0.0

    def test_multi_hop_path(self, sample_graph):
        """여러 홉 경로 검증"""
        path, dist = dijkstra(sample_graph, 1, 6)
        # 1→2→3→6 (5+4+3=12) vs 1→2→5→6 (5+3+4=12) — both are optimal
        assert path[0] == 1
        assert path[-1] == 6
        assert dist == 12.0

    def test_reverse_path_same_distance(self, sample_graph):
        """양방향 그래프: 정방향과 역방향 거리 동일"""
        _, dist_forward = dijkstra(sample_graph, 1, 10)
        _, dist_reverse = dijkstra(sample_graph, 10, 1)
        assert dist_forward == dist_reverse

    def test_nonexistent_node_raises(self, sample_graph):
        """존재하지 않는 노드 → HTTPException"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            dijkstra(sample_graph, 1, 999)

    def test_unreachable_node(self):
        """도달 불가 노드 → HTTPException"""
        from fastapi import HTTPException
        disconnected_graph = {
            1: [(2, 1.0)],
            2: [(1, 1.0)],
            3: [],  # 고립 노드
        }
        with pytest.raises(HTTPException):
            dijkstra(disconnected_graph, 1, 3)


class TestDijkstraAllPairs:
    """모든 쌍 최단 경로 테스트"""

    def test_all_pairs_count(self, sample_graph):
        """N개 노드 → N*(N-1)개 쌍"""
        target = [1, 3, 6, 10]
        result = dijkstra_all_pairs(sample_graph, target)
        assert len(result) == 4 * 3  # 12 pairs

    def test_all_pairs_symmetry(self, sample_graph):
        """양방향 그래프에서 (a,b)와 (b,a) 거리 동일"""
        target = [1, 5, 10]
        result = dijkstra_all_pairs(sample_graph, target)
        for a in target:
            for b in target:
                if a != b:
                    assert result[(a, b)][1] == result[(b, a)][1]

    def test_all_pairs_path_validity(self, sample_graph):
        """반환된 경로가 실제로 시작→끝 연결"""
        target = [1, 6, 10]
        result = dijkstra_all_pairs(sample_graph, target)
        for (src, dst), (path, dist) in result.items():
            if dist < float("inf"):
                assert path[0] == src
                assert path[-1] == dst


class TestTSP:
    """TSP 최적 방문 순서 테스트"""

    def test_no_waypoints(self, sample_graph):
        """경유지 없이 시작→종료 직행"""
        pair_dist = dijkstra_all_pairs(sample_graph, [1, 10])
        order, dist = solve_tsp([1, 10], start_node=1, end_node=10, pair_distances=pair_dist)
        assert order == [1, 10]
        assert dist == 19.0

    def test_single_waypoint(self, sample_graph):
        """경유지 1개: 입구→채소→계산대"""
        nodes = [1, 3, 10]
        pair_dist = dijkstra_all_pairs(sample_graph, nodes)
        order, dist = solve_tsp(nodes, start_node=1, end_node=10, pair_distances=pair_dist)
        assert order[0] == 1
        assert order[-1] == 10
        assert 3 in order
        assert len(order) == 3

    def test_multiple_waypoints_bruteforce(self, sample_graph):
        """경유지 3개 → 브루트포스 해 (≤8개)"""
        nodes = [1, 3, 5, 7, 10]
        pair_dist = dijkstra_all_pairs(sample_graph, nodes)
        order, dist = solve_tsp(nodes, start_node=1, end_node=10, pair_distances=pair_dist)

        # 검증: 시작/종료 맞는지, 모든 노드 포함
        assert order[0] == 1
        assert order[-1] == 10
        assert set(order) == {1, 3, 5, 7, 10}
        assert dist < float("inf")

    def test_bruteforce_optimality(self, sample_graph):
        """브루트포스가 진짜 최적 해인지 확인"""
        nodes = [1, 3, 6, 10]
        pair_dist = dijkstra_all_pairs(sample_graph, nodes)
        order, best_dist = solve_tsp(nodes, start_node=1, end_node=10, pair_distances=pair_dist)

        # 모든 순열의 거리 직접 계산
        from itertools import permutations
        waypoints = [3, 6]
        for perm in permutations(waypoints):
            route = [1] + list(perm) + [10]
            total = sum(
                _get_pair_distance(pair_dist, route[i], route[i+1])
                for i in range(len(route)-1)
            )
            assert best_dist <= total + 0.01  # 최적보다 작거나 같아야 함

    def test_nearest_neighbor_heuristic(self):
        """Nearest Neighbor 테스트 (9개 이상 경유지)"""
        # 직선 그래프: 1-2-3-...-12
        graph = {}
        for i in range(1, 13):
            graph[i] = []
            if i > 1:
                graph[i].append((i-1, 1.0))
            if i < 12:
                graph[i].append((i+1, 1.0))

        all_nodes = list(range(1, 13))
        pair_dist = dijkstra_all_pairs(graph, all_nodes)

        # 경유지 10개 (2~11) → nearest neighbor 사용
        order, dist = solve_tsp(all_nodes, start_node=1, end_node=12, pair_distances=pair_dist)
        assert order[0] == 1
        assert order[-1] == 12
        assert len(order) == 12
        assert dist < float("inf")

    def test_duplicate_waypoints_handled(self, sample_graph):
        """중복 경유지가 제거되는지"""
        nodes = [1, 3, 3, 6, 6, 10]  # 중복 포함
        pair_dist = dijkstra_all_pairs(sample_graph, list(set(nodes)))
        order, dist = solve_tsp(nodes, start_node=1, end_node=10, pair_distances=pair_dist)
        # 중복 제거 후 unique 경유지만 포함
        assert order[0] == 1
        assert order[-1] == 10
        assert len(set(order)) == len(order)  # 중복 없어야


class TestGetPairDistance:
    """거리 조회 헬퍼 테스트"""

    def test_same_node_zero(self):
        assert _get_pair_distance({}, 1, 1) == 0.0

    def test_known_pair(self):
        pd = {(1, 2): ([1, 2], 5.0)}
        assert _get_pair_distance(pd, 1, 2) == 5.0

    def test_unknown_pair_inf(self):
        assert _get_pair_distance({}, 1, 2) == float("inf")
