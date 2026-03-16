"""
테스트 공통 Fixture
- 순수 함수 테스트: DB 불필요
- API 통합 테스트: httpx AsyncClient + DB 의존성 오버라이드
"""
import os
import sys
import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── 공통 테스트 데이터 ──

TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_STORE_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TEST_SESSION_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
TEST_PRODUCT_ID_1 = uuid.UUID("44444444-4444-4444-4444-444444444001")
TEST_PRODUCT_ID_2 = uuid.UUID("44444444-4444-4444-4444-444444444002")
TEST_PRODUCT_ID_3 = uuid.UUID("44444444-4444-4444-4444-444444444003")


@pytest.fixture
def sample_graph():
    """테스트용 마트 공간 그래프 (10개 노드)

    Layout:
        1(입구) -- 2 -- 3 -- 4
                   |    |    |
                   5 -- 6 -- 7
                   |    |    |
                   8 -- 9 -- 10(계산대)
    """
    graph = {
        1: [(2, 5.0)],
        2: [(1, 5.0), (3, 4.0), (5, 3.0)],
        3: [(2, 4.0), (4, 3.0), (6, 3.0)],
        4: [(3, 3.0), (7, 4.0)],
        5: [(2, 3.0), (6, 4.0), (8, 3.0)],
        6: [(3, 3.0), (5, 4.0), (7, 4.0), (9, 3.0)],
        7: [(4, 4.0), (6, 4.0), (10, 3.0)],
        8: [(5, 3.0), (9, 4.0)],
        9: [(6, 3.0), (8, 4.0), (10, 4.0)],
        10: [(7, 3.0), (9, 4.0)],
    }
    return graph


@pytest.fixture
def sample_nodes_info():
    """그래프 노드 좌표 정보"""
    return {
        1: {"x": 0, "y": 0, "label": "입구", "node_type": "entrance", "floor": 1},
        2: {"x": 5, "y": 0, "label": "통로A", "node_type": "aisle", "floor": 1},
        3: {"x": 9, "y": 0, "label": "채소코너", "node_type": "shelf", "floor": 1},
        4: {"x": 12, "y": 0, "label": "과일코너", "node_type": "shelf", "floor": 1},
        5: {"x": 5, "y": 3, "label": "유제품", "node_type": "shelf", "floor": 1},
        6: {"x": 9, "y": 3, "label": "정육코너", "node_type": "shelf", "floor": 1},
        7: {"x": 12, "y": 3, "label": "수산코너", "node_type": "shelf", "floor": 1},
        8: {"x": 5, "y": 6, "label": "냉동식품", "node_type": "shelf", "floor": 1},
        9: {"x": 9, "y": 6, "label": "음료코너", "node_type": "shelf", "floor": 1},
        10: {"x": 12, "y": 6, "label": "계산대", "node_type": "checkout", "floor": 1},
    }


@pytest.fixture
def mock_db():
    """비동기 DB 세션 Mock"""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def test_jwt_token():
    """테스트용 JWT 토큰 생성"""
    from app.core.security import create_access_token
    return create_access_token(TEST_USER_ID, "테스트유저")
