@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo  Market Path Finder - 자동화 테스트 실행
echo ========================================
echo.

REM 가상환경 활성화
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM 테스트 의존성 설치
pip install httpx --quiet 2>nul

echo [1/3] 경로 알고리즘 테스트...
python -m pytest tests/test_pathfinding.py -v --tb=short
echo.

echo [2/3] 보안/인증 테스트...
python -m pytest tests/test_security.py -v --tb=short
echo.

echo [3/3] API 통합 테스트...
python -m pytest tests/test_api_integration.py -v --tb=short
echo.

echo ========================================
echo  전체 테스트 결과 요약
echo ========================================
python -m pytest tests/ -v --tb=short
echo.
pause
