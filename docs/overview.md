# Job Automation System

이 프로젝트는 취업 준비 업무를 자동화하기 위한 Python 기반 백엔드 초안이다.

## 구성

- `app/main.py`: 진입점
- `app/scheduler.py`: 서비스 실행 흐름
- `app/services/`: Notion, 리마인더, 채용 공고 수집, 추천 로직
- `app/db/sqlite.py`: SQLite 초기화 유틸리티
- `tests/`: 최소 동작 검증

## 다음 단계

- 실제 Notion API 클라이언트 연동
- 채용 사이트 수집기 추가
- 스케줄러를 cron 또는 APScheduler로 교체
