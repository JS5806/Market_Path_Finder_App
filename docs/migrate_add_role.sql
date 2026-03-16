-- 마이그레이션: users 테이블에 role 컬럼 추가
-- 기존 DB가 이미 실행 중인 경우 이 SQL을 실행하세요

-- role 컬럼 추가 (이미 있으면 무시)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'customer';

-- 기존 관리자 계정 role 업데이트 (이메일 도메인 기준)
UPDATE users SET role = 'admin'   WHERE email LIKE '%@admin.smartmart.com';
UPDATE users SET role = 'manager' WHERE email LIKE '%@manager.smartmart.com';
UPDATE users SET role = 'customer' WHERE role = 'customer'; -- 이미 기본값이지만 명시

-- 기본 테스트 계정 삽입 (비밀번호: demo1234)
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

SELECT 'Migration complete. Role column added and test accounts inserted.' AS result;
