# 취업 준비 자동화 시스템

Notion 데이터베이스를 운영 화면으로 사용하고, Python 애플리케이션이 채용 공고 조회, 마감일 기반 알림 분류, Discord 알림 전송, 만료 공고 정리 준비를 수행하는 자동화 프로젝트입니다.

## 프로젝트 개요

취업 준비 과정에서는 공고 확인, 상태 점검, 마감일 추적, 우선순위 정리 같은 반복 작업이 계속 발생합니다. 이 프로젝트는 그 반복 업무를 자동화해서, 사용자는 Notion에서 채용 공고를 관리하고 Python 애플리케이션은 필요한 알림과 후속 정리 작업을 담당하도록 설계되어 있습니다.

현재 구현 기준 핵심 방향은 다음과 같습니다.

- Notion DB를 채용 공고 운영 화면으로 사용
- Python 서비스가 공고 조회와 알림 로직 수행
- 마감일 기준 `D-7`, `D-3`, `D-1`, `D-day` 알림 대상 분류
- 알림 대상이 있으면 Discord Webhook 전송
- 지난 공고는 별도 목록으로 분리해 이후 `마감` 상태 업데이트 준비

## 현재 구현 기능

- Notion 채용 공고 조회
  - `notion-client`를 사용해 특정 Notion 데이터베이스에서 공고를 읽습니다.
  - `지원 공고명`, `기업명`, `직무`, `기업 규모`, `연봉/급여`, `진행상황`, `우선순위`, `채용 마감일` 컬럼을 기준으로 파싱합니다.
- 마감일 기반 알림 분류
  - `지원완료` 상태는 제외
  - 마감일이 없는 공고는 제외
  - 지난 공고는 `expired_jobs`로 분리
  - `D-7`, `D-3`, `D-1`, `D-day`만 `reminder_targets`에 포함
  - 우선순위 `상/중/하`는 모두 허용
- Discord 알림 발송
  - Discord Webhook 기반 알림 전송
  - 알림 대상이 1건 이상일 때만 전송
  - D-day 기준 이모지 강조 메시지 포맷 적용
  - 메시지 길이와 payload preview 로그 기록
- 콘솔 출력
  - 전체 Notion 공고 목록 출력
  - 알림 대상 공고 목록 별도 출력
- 만료 공고 정리 준비
  - `expired_jobs`는 `title`, `company`, `deadline`, `notion_page_id` 유지
  - 추후 Notion에서 삭제 대신 `진행상황 = 마감` 업데이트를 우선 적용할 수 있도록 함수 골격 제공
- 테스트 코드 포함
  - `reminder_service.py` 정책 테스트
  - 스케줄러 기본 동작 테스트

## 시스템 흐름

현재 메인 실행 흐름은 다음과 같습니다.

1. 실행 시 `logs/` 디렉터리를 자동 생성합니다.
2. SQLite를 초기화합니다.
3. Notion 데이터베이스에서 공고 목록을 조회합니다.
4. `ReminderService`가 공고를 `reminder_targets`와 `expired_jobs`로 분류합니다.
5. 콘솔에 전체 공고와 알림 대상 공고를 출력합니다.
6. `expired_jobs` 개수를 로그로 남깁니다.
7. `reminder_targets`가 있으면 Discord 알림을 발송합니다.
8. Discord 실패가 발생해도 프로그램은 종료되지 않고 로그만 남깁니다.

추가 운영 로그:

- `Scheduler execution timestamp`
- `Formatted Discord message length`
- `Discord payload preview (first 100 chars)`

## 기술 스택

- Python 3
- Notion API: `notion-client`
- 환경변수 관리: `python-dotenv`
- 스케줄러 확장 예정: `APScheduler`
- 테스트: `pytest`
- 저장소: SQLite

표준 라이브러리 사용:

- `datetime`
- `logging`
- `os`
- `sqlite3`
- `smtplib`
- `email.message`

## 프로젝트 구조

```text
job-automation-system/
├─ app/
│  ├─ main.py
│  ├─ scheduler.py
│  ├─ config.py
│  ├─ services/
│  │  ├─ notion_service.py
│  │  ├─ reminder_service.py
│  │  ├─ discord_service.py
│  │  ├─ email_service.py
│  │  ├─ job_collect_service.py
│  │  └─ recommendation_service.py
│  ├─ utils/
│  │  ├─ date_utils.py
│  │  └─ logger.py
│  └─ db/
│     └─ sqlite.py
├─ tests/
│  ├─ test_scheduler.py
│  └─ test_reminder_service.py
├─ docs/
├─ logs/
├─ requirements.txt
├─ .env.example
└─ README.md
```

주요 파일 역할:

- `app/main.py`
  - 전체 실행 오케스트레이션
  - 콘솔 출력, Discord 전송, 로그 디렉터리 생성 처리
- `app/services/notion_service.py`
  - Notion DB 조회
  - 만료 공고 상태 업데이트용 함수 골격 제공
- `app/services/reminder_service.py`
  - 마감일 기준 알림 정책 처리
  - `reminder_targets`, `expired_jobs` 분리
- `app/services/discord_service.py`
  - Discord 메시지 포맷팅
  - Discord Webhook 전송
- `app/services/email_service.py`
  - SMTP 이메일 로직 유지
  - 현재 기본 실행 흐름에서는 비활성화 상태

## 환경 변수

프로젝트는 `.env` 파일을 사용합니다. 예시는 [`.env.example`](/home/kimdaeho1998/job-automation-system/.env.example)에 정리되어 있습니다.

현재 사용 환경변수:

- `NOTION_API_KEY`
  - Notion API 인증 키
- `NOTION_DB_ID`
  - 조회할 Notion 데이터베이스 ID
- `DISCORD_ENABLED`
  - Discord 알림 사용 여부
- `DISCORD_WEBHOOK_URL`
  - Discord Webhook URL

유지 중인 추가 환경변수:

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USER`
- `EMAIL_PASSWORD`
- `EMAIL_TO`

이메일 기능은 코드에 남아 있지만 현재 기본 운영 알림 채널은 Discord입니다.

## 실행 방법

### 1. 가상환경 생성

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
cp .env.example .env
```

`.env`에 실제 운영 값을 입력합니다.

### 4. 애플리케이션 실행

```bash
python3 -m app.main
```

실행 시 현재 구현 기준으로 다음이 수행됩니다.

- Notion 공고 목록 조회
- 알림 대상/지난 공고 분류
- 콘솔 출력
- Discord 알림 발송 시도
- 만료 공고 개수 로그 출력
- `logs/` 디렉터리 자동 생성

## cron 자동 실행

운영 환경에서는 cron으로 하루 2회 실행할 수 있습니다. 프로젝트는 실행 시 `logs/` 폴더를 자동 생성하므로, cron 로그를 파일로 남기기 쉽게 구성되어 있습니다.

예시 cron 설정:

```cron
0 9 * * * cd /home/kimdaeho1998/job-automation-system && /home/kimdaeho1998/job-automation-system/.venv/bin/python -m app.main >> /home/kimdaeho1998/job-automation-system/logs/cron.log 2>&1
0 18 * * * cd /home/kimdaeho1998/job-automation-system && /home/kimdaeho1998/job-automation-system/.venv/bin/python -m app.main >> /home/kimdaeho1998/job-automation-system/logs/cron.log 2>&1
```

등록 방법:

```bash
crontab -e
```

운영 시 참고:

- 가상환경 Python 경로는 `.venv/bin/python`을 직접 지정합니다.
- cron 환경은 PATH가 제한적이므로 `cd` 후 절대경로 실행 방식을 권장합니다.
- Discord 전송 실패가 발생해도 프로그램은 종료되지 않고 로그에 남습니다.
- 로그는 `logs/cron.log`로 누적됩니다.

## 테스트

전체 테스트:

```bash
python3 -m pytest
```

리마인더 정책 테스트만 실행:

```bash
python3 -m pytest tests/test_reminder_service.py
```

현재 리마인더 테스트는 다음 정책을 검증합니다.

- `지원완료` 제외
- 마감일 없음 제외
- 지난 공고 분리
- `D-7`, `D-3`, `D-1`, `D-day`만 포함
- `D-2`, `D-5` 제외
- 우선순위 `상/중/하` 모두 허용
- 날짜 파싱 실패 시 제외

## 현재 구현 상태

현재 프로젝트는 다음 수준까지 구현되어 있습니다.

- Notion DB 조회 가능
- 마감일 기반 알림 정책 구현
- Discord Webhook 알림 구현
- 운영용 로그 강화
- cron 실행 준비 완료
- SMTP 이메일 발송 구조 유지
- 만료 공고 정리 대상 목록 생성 가능
- Notion 상태 업데이트 함수는 시그니처와 TODO 골격만 구현

아직 미구현 또는 확장 예정인 부분:

- 실제 만료 공고 `진행상황 = 마감` 업데이트 API 호출
- APScheduler 기반 정기 실행 연결
- 외부 채용 소스 수집 확장
- 추천 로직 고도화
- Discord 메시지 길이 초과 시 자동 분할 전송

## 향후 확장 계획

- 만료 공고 자동 상태 변경
  - `expired_jobs`를 Notion `마감` 상태로 일괄 업데이트
- 스케줄러 고도화
  - APScheduler 또는 cron 기반 정기 실행
- 알림 채널 확장
  - 이메일 외 Telegram, Slack 등 추가
- 지원 파이프라인 관리
  - 지원 예정, 지원 완료, 면접 진행, 결과 대기 자동 추적
- 분석 기능 추가
  - 지원 현황 통계, 응답률, 우선순위별 관리 대시보드
