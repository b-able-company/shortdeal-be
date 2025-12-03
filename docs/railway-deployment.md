# Railway 배포 계획

ShortDeal Django 백엔드(uvicorn/gunicorn 없이 `manage.py` 기반)를 Railway에 배포하기 위한 단계별 계획입니다. 실제 배포 전에 프로덕션 설정과 의존성을 보완하는 작업을 포함합니다.

## 1. 사전 준비
- Railway CLI 설치 및 로그인: `npm i -g @railway/cli && railway login`.
- 프로젝트 리포지토리를 Railway 프로젝트에 연결(GitHub 연동 또는 `railway init`).
- Postgres 플러그인 추가(`railway add` → Postgres) 후 DB 연결 정보를 환경 변수로 공유.
- 비밀 관리: `SECRET_KEY`, 이메일 크리덴셜 등은 Railway Variables로만 관리(레포에 커밋 금지).

## 2. 프로덕션 설정 보완(배포 전 코드 작업)
- `shortdeal/settings/production.py` 생성: `from .base import *` 후 아래를 적용합니다.
  - `DEBUG = False`.
  - `ALLOWED_HOSTS = [".railway.app", "127.0.0.1", "localhost"] + os.getenv("ALLOWED_HOSTS_EXTRA", "").split(",")`.
  - `DATABASES['default']`를 Railway Postgres 변수(`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`)에서 읽어오도록 구성.
  - 이메일 백엔드, 로깅 등은 환경 변수 기반으로 오버라이드.
- 의존성 추가: `gunicorn`(WSGI 서버)과 `whitenoise`(정적 파일 서빙)를 `requirements.txt`에 추가하고 WSGI에 `WhiteNoiseMiddleware` 삽입.
- Dockerfile/시작 커맨드 조정: Railway가 제공하는 `$PORT`에 바인딩하도록 `CMD gunicorn shortdeal.wsgi:application --bind 0.0.0.0:$PORT` 형태로 교체하고 `collectstatic`는 빌드 단계에서 실행.

## 3. Railway 서비스 구성
1. **웹 서비스 배포 방식 결정**
   - GitHub 연결 시: Railway Dashboard에서 리포를 선택하고 `Dockerfile` 빌드 옵션을 사용.
   - CLI 배포 시: 루트에서 `railway up --service web` 실행(Dockerfile 자동 감지).
2. **환경 변수 설정(Variables)**
   - `DJANGO_SETTINGS_MODULE=shortdeal.settings.production`
   - `SECRET_KEY=<랜덤 시크릿>`
   - `DEBUG=False`
   - `ALLOWED_HOSTS_EXTRA=<커스텀 도메인 필요 시>`
   - DB 연결 정보: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`(Railway Postgres 플러그인에서 복사).
   - 필요 시 이메일 관련 값(`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`).
   - `RAILWAY_STATIC_URL` 등 별도 스토리지 사용 시 추가 환경 변수를 정의.
3. **빌드 & 런타임 설정**
   - `Start Command`: `gunicorn shortdeal.wsgi:application --bind 0.0.0.0:$PORT`로 설정.
   - `Health Check`: `/` 혹은 `/api/v1/health`(헬스 엔드포인트 추가 시)로 설정.

## 4. 최초 배포 절차
1. `railway up` 또는 GitHub PR/브랜치 배포 트리거 → 컨테이너 빌드 완료 확인.
2. 마이그레이션: `railway run python manage.py migrate --settings=shortdeal.settings.production`.
3. 정적 파일 수집(추가 CDN/스토리지 미사용 시): `railway run python manage.py collectstatic --noinput --settings=shortdeal.settings.production`.
4. 관리자 계정 생성: `railway run python manage.py createsuperuser --settings=shortdeal.settings.production`.

## 5. 관측 및 운영
- 로그: `railway logs`로 WSGI/애플리케이션 로그 확인.
- DB 백업: Railway Postgres에서 제공하는 백업 스냅샷 기능을 주기적으로 활성화.
- 확장: 트래픽 증가 시 Railway 서비스 설정에서 인스턴스 사이즈/자동 리스타트 정책 조정.
- 도메인: 커스텀 도메인 연결 시 Railway 도메인에 CNAME 설정 후 `ALLOWED_HOSTS_EXTRA`에 도메인 추가.

## 6. 체크리스트
- [ ] `production.py` 및 Dockerfile 업데이트 커밋 완료.
- [ ] `gunicorn`/`whitenoise` 의존성 반영 및 정적 파일 서빙 확인.
- [ ] Railway Variables에 모든 비밀/DB 값 세팅.
- [ ] 마이그레이션 & collectstatic 실행 로그 확인.
- [ ] 관리자 계정 생성 및 기본 기능 수동 점검.
