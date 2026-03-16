# =============================================================================
# Market Path Finder - Backend Dockerfile
# FastAPI + Uvicorn (Python 3.12)
# =============================================================================
FROM python:3.12-slim

WORKDIR /app

# 시스템 패키지 (PostgreSQL 클라이언트, 빌드 도구)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 포트 노출
EXPOSE 8080

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
