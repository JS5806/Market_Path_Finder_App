"""
Step 10 — API 통합 테스트
httpx AsyncClient + FastAPI TestClient 사용
DB 의존성을 Mock으로 오버라이드하여 테스트
"""
import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db
from app.core.security import get_current_user_id, create_access_token

from tests.conftest import (
    TEST_USER_ID, TEST_STORE_ID, TEST_SESSION_ID,
    TEST_PRODUCT_ID_1, TEST_PRODUCT_ID_2,
)


# ── DB 의존성 오버라이드 ──

async def override_get_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    db.add = MagicMock()
    yield db


async def override_get_current_user_id():
    return TEST_USER_ID


# 앱 의존성 오버라이드 적용
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user_id] = override_get_current_user_id


# ── Fixtures ──

@pytest_asyncio.fixture
async def client():
    """httpx AsyncClient for testing"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """인증 헤더"""
    token = create_access_token(TEST_USER_ID, "테스트유저")
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════
#  Health Check
# ═══════════════════════════════════════════

class TestHealthCheck:

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """GET /health → 200"""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "market-path-finder-api"
        assert "version" in data


# ═══════════════════════════════════════════
#  사용자 API
# ═══════════════════════════════════════════

class TestUserAPI:

    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """POST /api/v1/users/register → 회원가입"""
        mock_user = MagicMock()
        mock_user.user_id = uuid.uuid4()
        mock_user.email = "new@test.com"
        mock_user.user_name = "신규유저"
        mock_user.age_group = "20s"
        mock_user.preferred_categories = ["과일"]
        mock_user.preferred_store_id = None
        mock_user.is_active = True
        mock_user.created_at = datetime.now(timezone.utc)

        with patch("app.api.v1.users.user_service.create_user", new_callable=AsyncMock, return_value=mock_user):
            resp = await client.post("/api/v1/users/register", json={
                "email": "new@test.com",
                "password": "password123",
                "user_name": "신규유저",
                "age_group": "20s",
                "preferred_categories": ["과일"],
            })
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        """잘못된 이메일 형식 → 422"""
        resp = await client.post("/api/v1/users/register", json={
            "email": "not-an-email",
            "password": "password123",
            "user_name": "유저",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client):
        """짧은 비밀번호 (min_length=6) → 422"""
        resp = await client.post("/api/v1/users/register", json={
            "email": "test@test.com",
            "password": "12345",
            "user_name": "유저",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        """POST /api/v1/users/login → 로그인"""
        mock_result = {
            "access_token": "eyJ.test.token",
            "token_type": "bearer",
            "user_id": TEST_USER_ID,
            "user_name": "테스트유저",
        }
        with patch("app.api.v1.users.user_service.authenticate_user", new_callable=AsyncMock, return_value=mock_result):
            resp = await client.post("/api/v1/users/login", json={
                "email": "test@test.com",
                "password": "password123",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "access_token" in data.get("data", data)

    @pytest.mark.asyncio
    async def test_profile_requires_auth(self, client):
        """GET /api/v1/users/me → 인증 없이 접근 불가"""
        # 의존성 오버라이드 일시 해제
        original = app.dependency_overrides.get(get_current_user_id)
        del app.dependency_overrides[get_current_user_id]
        try:
            resp = await client.get("/api/v1/users/me")
            assert resp.status_code in [401, 403]
        finally:
            if original:
                app.dependency_overrides[get_current_user_id] = original

    @pytest.mark.asyncio
    async def test_profile_with_auth(self, client, auth_headers):
        """GET /api/v1/users/me → 인증 시 프로필 반환"""
        mock_user = MagicMock()
        mock_user.user_id = TEST_USER_ID
        mock_user.email = "test@test.com"
        mock_user.user_name = "테스트유저"
        mock_user.age_group = "20s"
        mock_user.preferred_categories = ["과일"]
        mock_user.preferred_store_id = None
        mock_user.is_active = True
        mock_user.created_at = datetime.now(timezone.utc)

        with patch("app.api.v1.users.user_service.get_user_by_id", new_callable=AsyncMock, return_value=mock_user):
            resp = await client.get("/api/v1/users/me", headers=auth_headers)
            assert resp.status_code == 200


# ═══════════════════════════════════════════
#  장바구니 API
# ═══════════════════════════════════════════

class TestCartAPI:

    @pytest.mark.asyncio
    async def test_create_session(self, client, auth_headers):
        """POST /api/v1/cart/session → 장바구니 세션 생성"""
        mock_session = MagicMock()
        mock_session.session_id = TEST_SESSION_ID
        mock_session.user_id = TEST_USER_ID
        mock_session.store_id = TEST_STORE_ID
        mock_session.status = "active"
        mock_session.items = []
        mock_session.created_at = datetime.now(timezone.utc)

        with patch("app.api.v1.cart.cart_service.create_cart_session", new_callable=AsyncMock, return_value=mock_session):
            with patch("app.api.v1.cart.cart_service.build_cart_response", new_callable=AsyncMock, return_value={
                "session_id": str(TEST_SESSION_ID),
                "user_id": str(TEST_USER_ID),
                "store_id": str(TEST_STORE_ID),
                "status": "active",
                "items": [],
                "total_price": 0,
                "item_count": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }):
                resp = await client.post(
                    "/api/v1/cart/session",
                    json={"store_id": str(TEST_STORE_ID)},
                    headers=auth_headers,
                )
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_add_item(self, client, auth_headers):
        """POST /api/v1/cart/items → 아이템 추가"""
        mock_item = MagicMock()
        mock_item.item_id = 1
        mock_item.session_id = TEST_SESSION_ID
        mock_item.product_id = TEST_PRODUCT_ID_1
        mock_item.quantity = 2
        mock_item.source = "manual"
        mock_item.is_collected = False
        mock_item.added_at = datetime.now(timezone.utc)

        with patch("app.api.v1.cart.cart_service.add_item_to_cart", new_callable=AsyncMock, return_value=mock_item):
            resp = await client.post(
                "/api/v1/cart/items",
                json={
                    "product_id": str(TEST_PRODUCT_ID_1),
                    "quantity": 2,
                    "source": "manual",
                },
                headers=auth_headers,
            )
            assert resp.status_code in [200, 201]


# ═══════════════════════════════════════════
#  결제 API
# ═══════════════════════════════════════════

class TestPaymentAPI:

    @pytest.mark.asyncio
    async def test_qr_generate(self, client, auth_headers):
        """POST /api/v1/payment/qr-generate → QR 결제 생성"""
        mock_result = {
            "transaction_id": str(uuid.uuid4()),
            "qr_payload": '{"test": true}',
            "total_amount": 15000,
            "item_count": 3,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with patch("app.api.v1.payment.payment_service.create_qr_payment", new_callable=AsyncMock, return_value=mock_result):
            resp = await client.post(
                "/api/v1/payment/qr-generate",
                json={
                    "session_id": str(TEST_SESSION_ID),
                    "store_id": str(TEST_STORE_ID),
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_confirm_payment(self, client, auth_headers):
        """POST /api/v1/payment/confirm → 결제 승인"""
        mock_result = {
            "transaction_id": str(uuid.uuid4()),
            "status": "paid",
            "approval_number": "APR-20260316-001",
            "total_amount": 15000,
            "paid_at": datetime.now(timezone.utc).isoformat(),
        }
        with patch("app.api.v1.payment.payment_service.confirm_payment", new_callable=AsyncMock, return_value=mock_result):
            resp = await client.post(
                "/api/v1/payment/confirm",
                json={
                    "transaction_id": str(uuid.uuid4()),
                    "approval_number": "APR-20260316-001",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_transactions(self, client, auth_headers):
        """GET /api/v1/payment/transactions → 거래 내역"""
        with patch("app.api.v1.payment.payment_service.get_transactions", new_callable=AsyncMock, return_value=[]):
            resp = await client.get(
                "/api/v1/payment/transactions",
                headers=auth_headers,
            )
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_history(self, client, auth_headers):
        """GET /api/v1/payment/history → 쇼핑 히스토리"""
        with patch("app.api.v1.payment.payment_service.get_shopping_history", new_callable=AsyncMock, return_value=[]):
            resp = await client.get(
                "/api/v1/payment/history",
                headers=auth_headers,
            )
            assert resp.status_code == 200


# ═══════════════════════════════════════════
#  IoT API
# ═══════════════════════════════════════════

class TestIoTAPI:

    @pytest.mark.asyncio
    async def test_beacon_signal(self, client, auth_headers):
        """POST /api/v1/iot/beacon/signal → 비콘 신호 처리"""
        mock_result = {
            "estimated_x": 5.0,
            "estimated_y": 3.0,
            "floor": 1,
            "nearest_node_id": 5,
            "nearest_node_label": "유제품",
            "confidence": 0.85,
        }
        with patch("app.api.v1.iot.iot_service.estimate_position_from_beacon", new_callable=AsyncMock, return_value=mock_result):
            resp = await client.post(
                "/api/v1/iot/beacon/signal",
                json={
                    "store_id": str(TEST_STORE_ID),
                    "beacon_uuid": "test-uuid",
                    "major": 1,
                    "minor": 100,
                    "rssi": -65,
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_esl_update(self, client, auth_headers):
        """POST /api/v1/iot/esl/update → ESL 업데이트"""
        mock_result = {
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "product_name": "테스트 상품",
            "regular_price": 5000,
            "sale_price": 4500,
            "last_updated": None,
            "mqtt_sent": True,
        }
        with patch("app.api.v1.iot.iot_service.update_esl", new_callable=AsyncMock, return_value=mock_result):
            resp = await client.post(
                "/api/v1/iot/esl/update",
                json={
                    "mac_address": "AA:BB:CC:DD:EE:FF",
                    "product_name": "테스트 상품",
                    "regular_price": 5000,
                    "sale_price": 4500,
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200


# ═══════════════════════════════════════════
#  스키마 유효성 검사 테스트
# ═══════════════════════════════════════════

class TestSchemaValidation:

    def test_user_create_valid(self):
        """UserCreate 정상 데이터"""
        from app.schemas.user import UserCreate
        user = UserCreate(
            email="test@example.com",
            password="secure123",
            user_name="테스트",
            age_group="20s",
        )
        assert user.email == "test@example.com"
        assert user.user_name == "테스트"

    def test_user_create_invalid_email(self):
        """UserCreate 잘못된 이메일"""
        from app.schemas.user import UserCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UserCreate(email="not-email", password="secure123", user_name="유저")

    def test_user_create_short_password(self):
        """UserCreate 짧은 비밀번호"""
        from app.schemas.user import UserCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", password="123", user_name="유저")

    def test_user_create_empty_name(self):
        """UserCreate 빈 이름"""
        from app.schemas.user import UserCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", password="secure123", user_name="")

    def test_qr_payment_request_valid(self):
        """QrPaymentRequest 정상 데이터"""
        from app.schemas.payment import QrPaymentRequest
        req = QrPaymentRequest(
            session_id=uuid.uuid4(),
            store_id=uuid.uuid4(),
        )
        assert req.session_id is not None

    def test_payment_confirm_valid(self):
        """PaymentConfirmRequest 정상 데이터"""
        from app.schemas.payment import PaymentConfirmRequest
        req = PaymentConfirmRequest(
            transaction_id=uuid.uuid4(),
            approval_number="APR-001",
        )
        assert req.approval_number == "APR-001"

    def test_congestion_update_valid(self):
        """CongestionUpdateRequest 정상 데이터"""
        from app.schemas.congestion import CongestionUpdateRequest
        req = CongestionUpdateRequest(zone_id=1, density_level=3)
        assert req.density_level == 3

    def test_congestion_update_out_of_range(self):
        """CongestionUpdateRequest 범위 초과"""
        from app.schemas.congestion import CongestionUpdateRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CongestionUpdateRequest(zone_id=1, density_level=6)

    def test_congestion_update_below_range(self):
        """CongestionUpdateRequest 범위 미만"""
        from app.schemas.congestion import CongestionUpdateRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CongestionUpdateRequest(zone_id=1, density_level=0)

    def test_route_from_cart_has_avoid_congestion(self):
        """RouteFromCartRequest에 avoid_congestion 필드 존재"""
        from app.schemas.route import RouteFromCartRequest
        req = RouteFromCartRequest(
            store_id=uuid.uuid4(),
            avoid_congestion=True,
        )
        assert req.avoid_congestion is True


# ═══════════════════════════════════════════
#  혼잡도 API
# ═══════════════════════════════════════════

class TestCongestionAPI:

    @pytest.mark.asyncio
    async def test_get_congestion(self, client):
        """GET /api/v1/congestion/{store_id} → 혼잡도 조회"""
        with patch("app.api.v1.congestion.congestion_service.get_congestion", new_callable=AsyncMock, return_value=[]):
            resp = await client.get(f"/api/v1/congestion/{TEST_STORE_ID}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_congestion_summary(self, client):
        """GET /api/v1/congestion/{store_id}/summary → 혼잡도 요약"""
        mock_summary = {
            "store_id": str(TEST_STORE_ID),
            "total_zones": 5,
            "avg_density": 2.4,
            "most_congested": {"zone_name": "과일코너", "density_level": 4},
            "least_congested": {"zone_name": "냉동식품", "density_level": 1},
            "distribution": {1: 1, 2: 2, 3: 1, 4: 1, 5: 0},
        }
        with patch("app.api.v1.congestion.congestion_service.get_congestion_summary", new_callable=AsyncMock, return_value=mock_summary):
            resp = await client.get(f"/api/v1/congestion/{TEST_STORE_ID}/summary")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_congestion(self, client, auth_headers):
        """PUT /api/v1/congestion/{store_id} → 혼잡도 업데이트"""
        mock_result = {
            "congestion_id": 1,
            "zone_id": 3,
            "zone_name": "채소코너",
            "density_level": 4,
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "status": "updated",
        }
        with patch("app.api.v1.congestion.congestion_service.update_congestion", new_callable=AsyncMock, return_value=mock_result):
            resp = await client.put(
                f"/api/v1/congestion/{TEST_STORE_ID}",
                json={"zone_id": 3, "density_level": 4},
                headers=auth_headers,
            )
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_simulate_congestion(self, client, auth_headers):
        """POST /api/v1/congestion/{store_id}/simulate → 시뮬레이션"""
        with patch("app.api.v1.congestion.congestion_service.simulate_congestion", new_callable=AsyncMock, return_value=[]):
            resp = await client.post(
                f"/api/v1/congestion/{TEST_STORE_ID}/simulate",
                headers=auth_headers,
            )
            assert resp.status_code == 200
