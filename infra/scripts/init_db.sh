#!/bin/bash
# =============================================================================
# DB 초기화 스크립트 (라즈베리 파이 5에서 실행)
# Docker 없이 직접 PostgreSQL에 스키마를 적용할 때 사용
# =============================================================================

set -e

DB_NAME="mart_path_db"
DB_USER="mart_user"
DB_PASSWORD="${DB_PASSWORD:-changeme}"
SCHEMA_FILE="../../docs/schema_design.sql"

echo "[1/3] Creating database and user..."
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null || true

echo "[2/3] Applying schema..."
PGPASSWORD=${DB_PASSWORD} psql -U ${DB_USER} -d ${DB_NAME} -f ${SCHEMA_FILE}

echo "[3/3] Done! Database '${DB_NAME}' is ready."
