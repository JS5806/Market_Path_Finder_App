-- =============================================================================
-- Market Path Finder App - 초기 시드 데이터
-- 개발 및 테스트용 더미 데이터
-- =============================================================================

-- 1. 마트 지점 등록
INSERT INTO stores (store_id, store_name, address, open_time, close_time, floor_count, floor_info, width_meters, height_meters)
VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '스마트마트 강남점',
    '서울특별시 강남구 테헤란로 123',
    '09:00', '22:00', 1,
    '{"1F": "식료품 전관"}',
    40.00, 30.00
);

-- 2. 상품 카테고리 (계층형)
INSERT INTO product_categories (category_id, category_code, category_name, parent_id, depth) VALUES
(1, 'FOOD', '식품', NULL, 0),
(2, 'FOOD_MEAT', '정육', 1, 1),
(3, 'FOOD_MEAT_PORK', '돼지고기', 2, 2),
(4, 'FOOD_MEAT_BEEF', '소고기', 2, 2),
(5, 'FOOD_DAIRY', '유제품', 1, 1),
(6, 'FOOD_VEGGIE', '채소/과일', 1, 1),
(7, 'FOOD_SAUCE', '양념/소스', 1, 1),
(8, 'FOOD_DRINK', '음료', 1, 1),
(9, 'FOOD_SNACK', '과자/간식', 1, 1),
(10, 'DAILY', '생활용품', NULL, 0);

-- 3. 샘플 상품 등록
INSERT INTO products (product_id, sku, product_name, manufacturer, specification, category_id, description, nutrition_info, avg_rating) VALUES
('11111111-1111-1111-1111-111111111111', 'MEAT-001', '국내산 삼겹살', '한돈농장', '500g', 3, '신선한 국내산 삼겹살', '{"calories": 331, "protein": 17, "fat": 29}', 4.5),
('22222222-2222-2222-2222-222222222222', 'MEAT-002', '한우 등심 1++', '한우마을', '300g', 4, '최고급 한우 등심', '{"calories": 250, "protein": 26, "fat": 16}', 4.8),
('33333333-3333-3333-3333-333333333333', 'MEAT-003', '항정살', '한돈농장', '300g', 3, '부드러운 항정살', '{"calories": 290, "protein": 18, "fat": 24}', 4.6),
('44444444-4444-4444-4444-444444444444', 'SAUCE-001', '쌈장', '해찬들', '500g', 7, '전통 쌈장', '{"calories": 45, "sodium": 680}', 4.2),
('55555555-5555-5555-5555-555555555555', 'VEGGIE-001', '깻잎', '로컬팜', '30매', 6, '향긋한 깻잎', '{"calories": 12, "fiber": 3}', 4.0),
('66666666-6666-6666-6666-666666666666', 'VEGGIE-002', '대파', '로컬팜', '3단', 6, '파채용 대파', '{"calories": 15, "fiber": 2}', 3.9),
('77777777-7777-7777-7777-777777777777', 'VEGGIE-003', '마늘', '로컬팜', '300g', 6, '국내산 마늘', '{"calories": 20, "fiber": 1}', 4.3),
('88888888-8888-8888-8888-888888888888', 'DRINK-001', '소주 참이슬', '하이트진로', '360ml', 8, '대한민국 대표 소주', '{"calories": 64}', 4.1),
('99999999-9999-9999-9999-999999999999', 'DAIRY-001', '서울우유 1L', '서울우유', '1L', 5, '신선한 우유', '{"calories": 130, "protein": 6, "calcium": 200}', 4.4);

-- 4. 가격 정보
INSERT INTO product_prices (product_id, store_id, regular_price, sale_price, sale_end_date) VALUES
('11111111-1111-1111-1111-111111111111', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 15900, 12720, '2026-03-31'),
('22222222-2222-2222-2222-222222222222', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 42000, NULL, NULL),
('33333333-3333-3333-3333-333333333333', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 18900, NULL, NULL),
('44444444-4444-4444-4444-444444444444', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 4500, 3600, '2026-03-25'),
('55555555-5555-5555-5555-555555555555', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 2000, NULL, NULL),
('66666666-6666-6666-6666-666666666666', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 1500, NULL, NULL),
('77777777-7777-7777-7777-777777777777', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 5900, NULL, NULL),
('88888888-8888-8888-8888-888888888888', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 1800, 1500, '2026-03-20'),
('99999999-9999-9999-9999-999999999999', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 2800, NULL, NULL);

-- 5. 공간 노드 (매장 내 이동 지점 - 8x6 그리드 형태의 단순 매장)
-- 입구(0), 각 카테고리 구역 앞(1~6), 계산대(7)
INSERT INTO spatial_nodes (node_id, store_id, x, y, floor, node_type, label) VALUES
(1, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 20.0, 0.0,  1, 'entrance', '입구'),
(2, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 10.0, 5.0,  1, 'waypoint', '통로A'),
(3, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 30.0, 5.0,  1, 'waypoint', '통로B'),
(4, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 5.0,  10.0, 1, 'shelf', '채소/과일 코너'),
(5, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 15.0, 10.0, 1, 'shelf', '정육 코너'),
(6, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 25.0, 10.0, 1, 'shelf', '유제품 코너'),
(7, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 35.0, 10.0, 1, 'shelf', '양념/소스 코너'),
(8, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 10.0, 18.0, 1, 'shelf', '음료 코너'),
(9, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 30.0, 18.0, 1, 'shelf', '과자/간식 코너'),
(10, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 10.0, 25.0, 1, 'waypoint', '통로C'),
(11, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 30.0, 25.0, 1, 'waypoint', '통로D'),
(12, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 20.0, 28.0, 1, 'checkout', '계산대');

-- 6. 통로 간선 (노드 간 연결)
INSERT INTO spatial_edges (store_id, from_node_id, to_node_id, distance, is_bidirectional) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 1, 2,  11.18, TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 1, 3,  11.18, TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 2, 3,  20.00, TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 2, 4,  7.07,  TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 2, 5,  7.07,  TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 3, 6,  7.07,  TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 3, 7,  7.07,  TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 4, 5,  10.00, TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 5, 6,  10.00, TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 6, 7,  10.00, TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 4, 8,  9.43,  TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 7, 9,  9.43,  TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 8, 9,  20.00, TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 8, 10, 7.00,  TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 9, 11, 7.00,  TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 10, 11, 20.00, TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 10, 12, 10.44, TRUE),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 11, 12, 10.44, TRUE);

-- 7. 카테고리 구역 매핑
INSERT INTO category_zones (store_id, zone_name, category_code, x_start, y_start, x_end, y_end, floor, node_id) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '채소/과일 코너', 'FOOD_VEGGIE', 0, 8, 10, 14, 1, 4),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '정육 코너', 'FOOD_MEAT', 10, 8, 20, 14, 1, 5),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '유제품 코너', 'FOOD_DAIRY', 20, 8, 30, 14, 1, 6),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '양념/소스 코너', 'FOOD_SAUCE', 30, 8, 40, 14, 1, 7),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '음료 코너', 'FOOD_DRINK', 5, 15, 15, 22, 1, 8),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '과자/간식 코너', 'FOOD_SNACK', 25, 15, 35, 22, 1, 9);

-- 8. 상품-진열 위치 매핑
INSERT INTO product_locations (product_id, store_id, zone_id, node_id) VALUES
('11111111-1111-1111-1111-111111111111', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 2, 5),
('22222222-2222-2222-2222-222222222222', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 2, 5),
('33333333-3333-3333-3333-333333333333', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 2, 5),
('44444444-4444-4444-4444-444444444444', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 4, 7),
('55555555-5555-5555-5555-555555555555', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 1, 4),
('66666666-6666-6666-6666-666666666666', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 1, 4),
('77777777-7777-7777-7777-777777777777', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 1, 4),
('88888888-8888-8888-8888-888888888888', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 5, 8),
('99999999-9999-9999-9999-999999999999', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 3, 6);

-- 9. 레시피 시드 데이터
INSERT INTO recipes (recipe_id, recipe_name, description, difficulty, cooking_time_min, servings, instructions) VALUES
(1, '삼겹살 파티', '가족/친구와 함께하는 삼겹살 구이', 'easy', 30, 4,
 '[{"step":1,"text":"삼겹살을 먹기 좋은 크기로 잘라 준비합니다"},{"step":2,"text":"팬 또는 그릴에 삼겹살을 구워줍니다"},{"step":3,"text":"깻잎, 마늘, 쌈장과 함께 쌈을 싸서 먹습니다"}]'),
(2, '소고기 미역국', '생일에 먹는 따뜻한 미역국', 'medium', 60, 4,
 '[{"step":1,"text":"건미역을 물에 불립니다"},{"step":2,"text":"소고기를 참기름에 볶습니다"},{"step":3,"text":"불린 미역을 넣고 물을 부어 끓입니다"},{"step":4,"text":"간장으로 간을 맞추고 30분 더 끓입니다"}]');

-- 10. 레시피-재료 매핑
INSERT INTO recipe_ingredients (recipe_id, product_id, ingredient_name, quantity_text, is_essential) VALUES
(1, '11111111-1111-1111-1111-111111111111', '삼겹살', '500g', TRUE),
(1, '44444444-4444-4444-4444-444444444444', '쌈장', '적당량', TRUE),
(1, '55555555-5555-5555-5555-555555555555', '깻잎', '20매', TRUE),
(1, '66666666-6666-6666-6666-666666666666', '대파', '1단', FALSE),
(1, '77777777-7777-7777-7777-777777777777', '마늘', '1통', TRUE),
(1, '88888888-8888-8888-8888-888888888888', '소주', '1병', FALSE);

-- 11. 상품 연관성 데이터
INSERT INTO product_associations (product_a_id, product_b_id, score, reason) VALUES
('11111111-1111-1111-1111-111111111111', '44444444-4444-4444-4444-444444444444', 0.92, '삼겹살과 쌈장은 필수 조합'),
('11111111-1111-1111-1111-111111111111', '55555555-5555-5555-5555-555555555555', 0.88, '삼겹살에 깻잎 쌈'),
('11111111-1111-1111-1111-111111111111', '77777777-7777-7777-7777-777777777777', 0.85, '삼겹살 구울 때 마늘도 함께'),
('11111111-1111-1111-1111-111111111111', '88888888-8888-8888-8888-888888888888', 0.78, '삼겹살에 소주 한잔');

-- 12. AI 시스템 프롬프트
INSERT INTO ai_prompts (prompt_name, persona, tool_rules, response_format, version) VALUES
('shopping_assistant',
 '당신은 마트 쇼핑 도우미 AI입니다. 사용자가 요청한 재료나 레시피에 맞는 상품을 추천하고, 장바구니에 추가해주세요. 항상 친절하고 간결하게 응답하세요.',
 '{"allowed_tools": ["search_recipe", "search_product", "add_to_cart", "get_cart", "get_price"]}',
 '{"type": "object", "properties": {"message": {"type": "string"}, "recommendations": {"type": "array"}, "cart_updates": {"type": "array"}}}',
 1);

-- 12-1. 기본 계정 시드 (role 별 테스트 계정)
-- 비밀번호: demo1234 (bcrypt 해시)
INSERT INTO users (user_id, email, password_hash, user_name, role, is_active) VALUES
(
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'admin@admin.smartmart.com',
    '$2b$12$4bAmu6ouX9AcxkueW1yx0.j.YbnMdVkIgRQmPW1GCBo4TmuDoBkWe',
    '시스템관리자',
    'admin',
    true
),
(
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'mart@manager.smartmart.com',
    '$2b$12$BPPM4xFXjXhlRaBB.lOFEeEsKwRGuXJ0xSpvE2prpLLDSThLpxBI2',
    '강남점관리자',
    'manager',
    true
),
(
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'user@gmail.com',
    '$2b$12$7ZnaYjC0ay4MwsXFgx9BFOqdcfKbuUtyrT7Ipd4H5F2lGptl3ben2',
    '홍길동',
    'customer',
    true
)
ON CONFLICT (email) DO NOTHING;

-- 13. iBeacon 시드 데이터 (6개 비콘)
INSERT INTO beacons (store_id, uuid, major, minor, x, y, floor, tx_power, label) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'FDA50693-A4E2-4FB1-AFCF-C6EB07647825', 1, 1, 20.0, 0.0,  1, -59, '입구 비콘'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'FDA50693-A4E2-4FB1-AFCF-C6EB07647825', 1, 2, 5.0,  10.0, 1, -59, '채소 코너 비콘'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'FDA50693-A4E2-4FB1-AFCF-C6EB07647825', 1, 3, 35.0, 10.0, 1, -59, '소스 코너 비콘'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'FDA50693-A4E2-4FB1-AFCF-C6EB07647825', 1, 4, 5.0,  20.0, 1, -59, '음료 코너 비콘'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'FDA50693-A4E2-4FB1-AFCF-C6EB07647825', 1, 5, 35.0, 20.0, 1, -59, '간식 코너 비콘'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'FDA50693-A4E2-4FB1-AFCF-C6EB07647825', 1, 6, 20.0, 28.0, 1, -59, '계산대 비콘');
