"""
Step 10 — 인증/보안 단위 테스트
비밀번호 해싱, JWT 생성/검증
(순수 함수 테스트: DB 불필요)
"""
import uuid
import pytest
from datetime import timedelta

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)


class TestPasswordHashing:
    """비밀번호 해싱/검증 테스트"""

    def test_hash_creates_different_string(self):
        """해싱 결과가 원문과 다름"""
        plain = "myPassword123!"
        hashed = hash_password(plain)
        assert hashed != plain
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        """올바른 비밀번호 검증 성공"""
        plain = "securePassword456"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        """잘못된 비밀번호 검증 실패"""
        hashed = hash_password("correctPassword")
        assert verify_password("wrongPassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        """같은 비밀번호도 매번 다른 해시 (salt)"""
        plain = "samePassword"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        assert hash1 != hash2  # bcrypt는 salt 사용
        # 둘 다 검증은 성공
        assert verify_password(plain, hash1)
        assert verify_password(plain, hash2)

    def test_unicode_password(self):
        """한글 비밀번호 지원"""
        plain = "안녕하세요비밀번호123"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed)


class TestJWT:
    """JWT 토큰 생성/검증 테스트"""

    def test_create_and_decode_token(self):
        """토큰 생성 후 디코드 시 올바른 정보"""
        user_id = uuid.uuid4()
        user_name = "테스트유저"
        token = create_access_token(user_id, user_name)

        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["name"] == user_name
        assert "exp" in payload

    def test_token_is_string(self):
        """토큰이 문자열(eyJ...)로 반환됨"""
        token = create_access_token(uuid.uuid4(), "user")
        assert isinstance(token, str)
        assert token.startswith("eyJ")

    def test_custom_expiration(self):
        """커스텀 만료 시간 설정"""
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "user", expires_delta=timedelta(minutes=5))
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)

    def test_invalid_token_raises(self):
        """잘못된 토큰 → HTTPException"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises(self):
        """변조된 토큰 → HTTPException"""
        from fastapi import HTTPException
        token = create_access_token(uuid.uuid4(), "user")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException):
            decode_token(tampered)

    def test_different_users_different_tokens(self):
        """다른 사용자는 다른 토큰"""
        t1 = create_access_token(uuid.uuid4(), "userA")
        t2 = create_access_token(uuid.uuid4(), "userB")
        assert t1 != t2
