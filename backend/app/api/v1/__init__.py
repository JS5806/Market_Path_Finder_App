"""
API v1 라우터 통합
"""
from fastapi import APIRouter

from app.api.v1.products import router as products_router
from app.api.v1.users import router as users_router
from app.api.v1.cart import router as cart_router
from app.api.v1.route import router as route_router
from app.api.v1.ai import router as ai_router
from app.api.v1.iot import router as iot_router
from app.api.v1.payment import router as payment_router
from app.api.v1.congestion import router as congestion_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(products_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(cart_router)
api_v1_router.include_router(route_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(iot_router)
api_v1_router.include_router(payment_router)
api_v1_router.include_router(congestion_router)
