-- =============================================================================
-- Market Path Finder App - PostgreSQL Schema Design
-- 마트 최적 경로 추천 쇼핑 앱 데이터베이스 스키마
-- Target: Raspberry Pi 5 (PostgreSQL 15+)
-- =============================================================================

-- 확장 모듈
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. 마트 및 공간 데이터 (Store & Spatial Data)
-- =============================================================================

-- 1-1) 지점 정보
CREATE TABLE stores (
    store_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_name      VARCHAR(100) NOT NULL,
    address         VARCHAR(255) NOT NULL,
    open_time       TIME NOT NULL DEFAULT '09:00',
    close_time      TIME NOT NULL DEFAULT '22:00',
    floor_count     INTEGER NOT NULL DEFAULT 1,
    floor_info      JSONB,           -- 층별 안내 (예: {"1F": "식료품", "2F": "생활용품"})
    width_meters    NUMERIC(8,2),    -- 매장 가로 크기 (m)
    height_meters   NUMERIC(8,2),    -- 매장 세로 크기 (m)
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 1-2) 공간 노드 (매장 내 이동 가능한 지점)
CREATE TABLE spatial_nodes (
    node_id         SERIAL PRIMARY KEY,
    store_id        UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    x               NUMERIC(8,2) NOT NULL,   -- X 좌표
    y               NUMERIC(8,2) NOT NULL,   -- Y 좌표
    floor           INTEGER NOT NULL DEFAULT 1,
    node_type       VARCHAR(30) NOT NULL DEFAULT 'waypoint',
        -- waypoint: 이동 지점, shelf: 진열대, entrance: 출입구, checkout: 계산대
    label           VARCHAR(100),            -- 사람이 읽을 수 있는 이름
    is_obstacle     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_spatial_nodes_store ON spatial_nodes(store_id);

-- 1-3) 통로 간선 (노드 간 이동 가능한 연결)
CREATE TABLE spatial_edges (
    edge_id         SERIAL PRIMARY KEY,
    store_id        UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    from_node_id    INTEGER NOT NULL REFERENCES spatial_nodes(node_id) ON DELETE CASCADE,
    to_node_id      INTEGER NOT NULL REFERENCES spatial_nodes(node_id) ON DELETE CASCADE,
    distance        NUMERIC(8,2) NOT NULL,   -- 물리적 거리 (m)
    weight          NUMERIC(8,2),            -- 가중치 (혼잡도 반영 시)
    is_bidirectional BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_spatial_edges_store ON spatial_edges(store_id);
CREATE INDEX idx_spatial_edges_from ON spatial_edges(from_node_id);
CREATE INDEX idx_spatial_edges_to ON spatial_edges(to_node_id);

-- 1-4) 카테고리 구역 (매장 내 영역별 카테고리 매핑)
CREATE TABLE category_zones (
    zone_id         SERIAL PRIMARY KEY,
    store_id        UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    zone_name       VARCHAR(100) NOT NULL,   -- "육류 코너", "유제품 코너"
    category_code   VARCHAR(50) NOT NULL,    -- 해당 구역의 상품 카테고리 코드
    x_start         NUMERIC(8,2) NOT NULL,
    y_start         NUMERIC(8,2) NOT NULL,
    x_end           NUMERIC(8,2) NOT NULL,
    y_end           NUMERIC(8,2) NOT NULL,
    floor           INTEGER NOT NULL DEFAULT 1,
    node_id         INTEGER REFERENCES spatial_nodes(node_id), -- 가장 가까운 노드
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_category_zones_store ON category_zones(store_id);

-- 1-5) 실시간 혼잡도 (더미 데이터 포함)
CREATE TABLE congestion_data (
    congestion_id   SERIAL PRIMARY KEY,
    store_id        UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    zone_id         INTEGER REFERENCES category_zones(zone_id),
    density_level   INTEGER NOT NULL DEFAULT 1 CHECK (density_level BETWEEN 1 AND 5),
        -- 1: 한산, 5: 매우 혼잡
    measured_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 2. 상품 마스터 데이터 (Product Master Data)
-- =============================================================================

-- 2-1) 상품 카테고리 (계층형)
CREATE TABLE product_categories (
    category_id     SERIAL PRIMARY KEY,
    category_code   VARCHAR(50) UNIQUE NOT NULL,
    category_name   VARCHAR(100) NOT NULL,
    parent_id       INTEGER REFERENCES product_categories(category_id),
    depth           INTEGER NOT NULL DEFAULT 0,   -- 0: 대분류, 1: 중분류, 2: 소분류
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2-2) 상품 마스터
CREATE TABLE products (
    product_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku             VARCHAR(50) UNIQUE NOT NULL,     -- 상품 고유 식별 코드
    product_name    VARCHAR(200) NOT NULL,
    manufacturer    VARCHAR(100),
    specification   VARCHAR(100),                    -- 규격 (300g, 500ml 등)
    category_id     INTEGER REFERENCES product_categories(category_id),
    description     TEXT,
    nutrition_info  JSONB,   -- {"calories": 250, "sugar": 5, "protein": 20, ...}
    expiry_days     INTEGER,                         -- 유통기한 (일 수)
    image_thumb_url VARCHAR(500),
    image_detail_url VARCHAR(500),
    avg_rating      NUMERIC(3,2) DEFAULT 0.00,
    review_count    INTEGER DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id);

-- 2-3) 상품 리뷰
CREATE TABLE product_reviews (
    review_id       SERIAL PRIMARY KEY,
    product_id      UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    user_id         UUID,  -- users 테이블 참조 (아래 정의)
    rating          INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2-4) 상품-진열 위치 매핑 (상품이 매장 내 어디에 있는지)
CREATE TABLE product_locations (
    location_id     SERIAL PRIMARY KEY,
    product_id      UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    store_id        UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    zone_id         INTEGER REFERENCES category_zones(zone_id),
    node_id         INTEGER REFERENCES spatial_nodes(node_id), -- 해당 상품의 가장 가까운 노드
    shelf_info      VARCHAR(100),   -- 진열대 번호 등
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_product_locations_product ON product_locations(product_id);
CREATE INDEX idx_product_locations_store ON product_locations(store_id);

-- =============================================================================
-- 3. 실시간 가격 및 재고 데이터 (Price & Inventory)
-- =============================================================================

-- 3-1) 가격 정보
CREATE TABLE product_prices (
    price_id        SERIAL PRIMARY KEY,
    product_id      UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    store_id        UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    regular_price   INTEGER NOT NULL,                -- 정상가 (원)
    sale_price      INTEGER,                         -- 행사가 (원, NULL이면 행사 없음)
    sale_end_date   DATE,                            -- 행사 종료일
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_product_prices_product ON product_prices(product_id, store_id);

-- 3-2) 재고 상태
CREATE TABLE inventory (
    inventory_id    SERIAL PRIMARY KEY,
    product_id      UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    store_id        UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    quantity        INTEGER NOT NULL DEFAULT 0,
    is_sold_out     BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_inventory_product ON inventory(product_id, store_id);

-- 3-3) ESL (전자가격표) 장치 정보
CREATE TABLE esl_devices (
    esl_id          SERIAL PRIMARY KEY,
    mac_address     VARCHAR(17) UNIQUE NOT NULL,     -- MAC 주소 (XX:XX:XX:XX:XX:XX)
    store_id        UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    product_id      UUID REFERENCES products(product_id),  -- 페어링된 상품
    battery_level   INTEGER DEFAULT 100 CHECK (battery_level BETWEEN 0 AND 100),
    last_sync_at    TIMESTAMPTZ,
    is_online       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 4. 사용자 및 활동 데이터 (User & Activity Data)
-- =============================================================================

-- 4-1) 사용자 프로필
CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,           -- bcrypt 해싱
    user_name       VARCHAR(50) NOT NULL,
    age_group       VARCHAR(10),                     -- '10대', '20대', '30대' ...
    preferred_categories JSONB,                      -- ["정육", "유제품", ...]
    preferred_store_id   UUID REFERENCES stores(store_id),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4-2) 장바구니 세션
CREATE TABLE cart_sessions (
    session_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    store_id        UUID REFERENCES stores(store_id),
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
        -- active, completed, cancelled
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_cart_sessions_user ON cart_sessions(user_id);

-- 4-3) 장바구니 아이템
CREATE TABLE cart_items (
    item_id         SERIAL PRIMARY KEY,
    session_id      UUID NOT NULL REFERENCES cart_sessions(session_id) ON DELETE CASCADE,
    product_id      UUID NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source          VARCHAR(20) NOT NULL DEFAULT 'manual',
        -- manual: 수동 추가, ai: AI 추천, nfc: NFC 태깅
    is_collected    BOOLEAN NOT NULL DEFAULT FALSE    -- 실제로 집었는지 여부
);
CREATE INDEX idx_cart_items_session ON cart_items(session_id);

-- 4-4) 쇼핑 히스토리 (구매 내역 요약)
CREATE TABLE shopping_history (
    history_id      SERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    store_id        UUID NOT NULL REFERENCES stores(store_id),
    session_id      UUID REFERENCES cart_sessions(session_id),
    total_amount    INTEGER NOT NULL DEFAULT 0,
    item_count      INTEGER NOT NULL DEFAULT 0,
    shopped_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_shopping_history_user ON shopping_history(user_id);

-- =============================================================================
-- 5. AI 추론 및 추천 데이터 (AI Inference & Recommendation)
-- =============================================================================

-- 5-1) 레시피 데이터
CREATE TABLE recipes (
    recipe_id       SERIAL PRIMARY KEY,
    recipe_name     VARCHAR(200) NOT NULL,
    description     TEXT,
    difficulty      VARCHAR(10) NOT NULL DEFAULT 'easy',
        -- easy, medium, hard
    cooking_time_min INTEGER,
    servings        INTEGER DEFAULT 2,
    instructions    JSONB,   -- [{"step": 1, "text": "..."}, ...]
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5-2) 레시피-재료 매핑
CREATE TABLE recipe_ingredients (
    id              SERIAL PRIMARY KEY,
    recipe_id       INTEGER NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    product_id      UUID REFERENCES products(product_id),  -- 매칭 가능한 상품
    ingredient_name VARCHAR(100) NOT NULL,                  -- 재료명 (상품 매칭 안 될 수도 있음)
    quantity_text   VARCHAR(50),                            -- "200g", "2큰술"
    is_essential    BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_recipe_ingredients_recipe ON recipe_ingredients(recipe_id);

-- 5-3) 상품 연관성 (함께 구매할 확률이 높은 상품 쌍)
CREATE TABLE product_associations (
    association_id  SERIAL PRIMARY KEY,
    product_a_id    UUID NOT NULL REFERENCES products(product_id),
    product_b_id    UUID NOT NULL REFERENCES products(product_id),
    score           NUMERIC(5,4) NOT NULL DEFAULT 0.0,  -- 연관성 점수 (0~1)
    reason          VARCHAR(200),    -- "삼겹살과 함께 자주 구매됨"
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (product_a_id, product_b_id)
);

-- 5-4) AI 시스템 프롬프트 관리
CREATE TABLE ai_prompts (
    prompt_id       SERIAL PRIMARY KEY,
    prompt_name     VARCHAR(100) UNIQUE NOT NULL,    -- 'shopping_assistant', 'recipe_recommender'
    persona         TEXT NOT NULL,                    -- 에이전트 페르소나
    tool_rules      JSONB,                           -- 도구 사용 규칙
    response_format JSONB,                           -- JSON 응답 형식 정의
    version         INTEGER NOT NULL DEFAULT 1,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5-5) AI 대화 로그
CREATE TABLE ai_chat_logs (
    log_id          SERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(user_id),
    session_id      UUID REFERENCES cart_sessions(session_id),
    role            VARCHAR(20) NOT NULL,    -- 'user', 'assistant', 'system'
    content         TEXT NOT NULL,
    tool_calls      JSONB,                   -- MCP 도구 호출 기록
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_ai_chat_logs_user ON ai_chat_logs(user_id);

-- =============================================================================
-- 6. 결제 및 인증 데이터 (Payment & Transaction)
-- =============================================================================

-- 6-1) 결제 트랜잭션
CREATE TABLE transactions (
    transaction_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(user_id),
    session_id      UUID NOT NULL REFERENCES cart_sessions(session_id),
    store_id        UUID NOT NULL REFERENCES stores(store_id),
    total_amount    INTEGER NOT NULL,
    payment_method  VARCHAR(30) NOT NULL DEFAULT 'qr_code',   -- qr_code, virtual
    approval_number VARCHAR(50),
    qr_payload      TEXT,            -- 암호화된 QR 데이터
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
        -- pending, approved, rejected, refunded
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_session ON transactions(session_id);

-- =============================================================================
-- 7. IoT 장치 데이터 (Beacon / NFC)
-- =============================================================================

-- 7-1) iBeacon 장치 등록
CREATE TABLE beacons (
    beacon_id       SERIAL PRIMARY KEY,
    store_id        UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    uuid            VARCHAR(36) NOT NULL,
    major           INTEGER NOT NULL,
    minor           INTEGER NOT NULL,
    x               NUMERIC(8,2) NOT NULL,   -- 설치 X 좌표
    y               NUMERIC(8,2) NOT NULL,   -- 설치 Y 좌표
    floor           INTEGER NOT NULL DEFAULT 1,
    tx_power        INTEGER DEFAULT -59,     -- 1m 기준 RSSI
    label           VARCHAR(100),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7-2) NFC 태그-상품 페어링
CREATE TABLE nfc_tags (
    nfc_tag_id      SERIAL PRIMARY KEY,
    tag_uid         VARCHAR(30) UNIQUE NOT NULL,     -- NFC 태그 고유 ID
    store_id        UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    product_id      UUID REFERENCES products(product_id),
    location_desc   VARCHAR(200),    -- "육류 코너 3번 진열대"
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 8. 경로 계산 결과 캐시
-- =============================================================================
CREATE TABLE route_results (
    route_id        SERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(user_id),
    session_id      UUID REFERENCES cart_sessions(session_id),
    store_id        UUID NOT NULL REFERENCES stores(store_id),
    visit_order     JSONB NOT NULL,  -- [{"node_id": 1, "product_id": "...", "x": 10, "y": 20}, ...]
    total_distance  NUMERIC(10,2),   -- 총 이동 예상 거리 (m)
    algorithm       VARCHAR(30) NOT NULL DEFAULT 'dijkstra',
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 트리거: updated_at 자동 갱신
-- =============================================================================
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_stores_updated BEFORE UPDATE ON stores
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER trg_products_updated BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER trg_cart_sessions_updated BEFORE UPDATE ON cart_sessions
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER trg_ai_prompts_updated BEFORE UPDATE ON ai_prompts
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER trg_product_prices_updated BEFORE UPDATE ON product_prices
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER trg_inventory_updated BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
