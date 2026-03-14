🛒 Market Path Finder App (마트 최적 경로 추천 쇼핑 앱)

배재대학교 캡스톤 디자인 프로젝트
AI와 IoT 기술을 활용한 스마트 마트 쇼핑 솔루션입니다.

🛠 Tech Stack
- Main: Python (FastAPI), C++ (Arduino/ESP32), JavaScript/TypeScript (React Native)
- Infrastructure: Raspberry Pi 5, 4070 Ti PC (Local LLM), PostgreSQL, MQTT Broker 
- Core_Tech: MCP (Model Context Protocol), ReAct Pattern, IPS (Indoor Positioning System), Dijkstra/TSP Algorithm

📂 Project Structure
- backend/: FastAPI 기반 AI 에이전트 및 CRUD API
- embedded/: ESP32, iBeacon, E-Ink 디스플레이 제어 코드
- frontend/: React Native 모바일 앱 UI 및 NFC 연동
- infra: 라즈베리 파이 서버 및 DB 설정 파일
- docs/: 기획 문서 및 데이터 명세서

🤝 Contribution Rules
1. 모든 기능 개발은 `feature/기능이름` 브랜치에서 진행합니다.
2. `main` 브랜치로 합칠 때는 반드시 **Pull Request(PR)**를 생성해야 합니다.
3. 팀장의 승인(Approve) 후 최종 Merge가 가능합니다.
