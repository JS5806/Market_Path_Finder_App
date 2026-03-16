"""
Market Path Finder App - FastAPI Entry Point
라즈베리 파이 5에서 실행되는 메인 API 서버
"""
import logging
from contextlib import asynccontextmanager

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1 import api_v1_router
from app.services.mqtt_service import mqtt_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 MQTT 연결 관리"""
    # Startup - MQTT는 선택적 (Mosquitto 없어도 API 정상 동작)
    try:
        mqtt_ok = mqtt_service.connect()
        if mqtt_ok:
            logger.info("MQTT connection initiated")
        else:
            logger.warning("MQTT broker not available - IoT features will be limited")
    except Exception as e:
        logger.warning(f"MQTT setup skipped: {e}")

    yield

    # Shutdown
    logger.info("Shutting down MQTT...")
    mqtt_service.disconnect()


app = FastAPI(
    title="Market Path Finder API",
    description="마트 최적 경로 추천 쇼핑 앱 백엔드 API",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS 설정 (React Native 앱 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 라우터 등록
app.include_router(api_v1_router)

# 정적 파일 서빙 (평면도 이미지 등)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "market-path-finder-api",
        "version": "0.2.0",
        "mqtt_connected": mqtt_service.connected,
    }
