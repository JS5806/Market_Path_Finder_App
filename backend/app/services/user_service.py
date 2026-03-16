"""
사용자 서비스 - 회원가입, 로그인, 프로필 조회
역할(role)은 이메일 도메인으로 자동 결정:
  @admin.smartmart.com → admin (프로그램 관리자)
  @manager.smartmart.com → manager (마트 관리자)
  그 외 → customer (일반 사용자)
"""
from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, create_access_token


def determine_role(email: str) -> str:
    """이메일 도메인으로 역할(role) 자동 결정"""
    domain = email.split("@")[-1].lower()
    if domain == "admin.smartmart.com":
        return "admin"
    elif domain == "manager.smartmart.com":
        return "manager"
    else:
        return "customer"


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    """회원가입 - 이메일 도메인에 따라 역할 자동 부여"""
    # 이메일 중복 확인
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 가입된 이메일입니다")

    role = determine_role(data.email)

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        user_name=data.user_name,
        role=role,
        age_group=data.age_group,
        preferred_categories=data.preferred_categories,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> dict:
    """로그인 → JWT 토큰 발급 (role 포함)"""
    result = await db.execute(select(User).where(User.email == email, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
        )

    token = create_access_token(user.user_id, user.user_name, role=user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "user_name": user.user_name,
        "role": user.role,
    }


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """사용자 ID로 프로필 조회"""
    result = await db.execute(select(User).where(User.user_id == user_id, User.is_active == True))
    return result.scalar_one_or_none()
