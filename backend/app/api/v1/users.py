"""
사용자 API 라우터
- 회원가입, 로그인, 프로필 조회
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.common import ApiResponse
from app.schemas.user import UserCreate, UserLogin, TokenOut, UserOut
from app.services import user_service

router = APIRouter(prefix="/users", tags=["사용자"])


@router.post("/register", response_model=ApiResponse[UserOut])
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """회원가입"""
    user = await user_service.create_user(db, data)
    return ApiResponse(message="회원가입이 완료되었습니다", data=UserOut.model_validate(user))


@router.post("/login", response_model=ApiResponse[TokenOut])
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """로그인 → JWT 토큰 발급"""
    result = await user_service.authenticate_user(db, data.email, data.password)
    return ApiResponse(data=TokenOut(**result))


@router.get("/me", response_model=ApiResponse[UserOut])
async def get_my_profile(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """내 프로필 조회 (JWT 인증 필요)"""
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        return ApiResponse(success=False, message="사용자를 찾을 수 없습니다")
    return ApiResponse(data=UserOut.model_validate(user))
