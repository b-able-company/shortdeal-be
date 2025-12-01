# ShortDeal Implementation Plan

## Scope & Guardrails
- Deliver P0 items only (docs/func-spec.md, 65 features) using Django 4.2, DRF, JWT, PostgreSQL.
- Follow response envelope `{success, data, message, pagination?, meta?}` and base URL `/api/v1/`.
- Enforce business rules: producer signup → booth auto-create, single pending offer per content/buyer, offer accept → LOI auto-create, onboarding gate, email notifications, soft delete via `status='deleted'`.
- No raw SQL, no custom user beyond AbstractUser extension, UTC timestamps, ArrayField for tags, foreign keys default CASCADE.

## Required Validations (done before coding)
- **Edge case analysis**
  - Auth/Onboarding: duplicate email, weak/ mismatched passwords, role change attempts, onboarding re-entry after completion, invalid logo/thumbnail (type/size), slug collisions for booths, onboarding access when not authenticated or wrong role.
  - Content browsing: invalid filters (price range inversion, bad currency), accessing deleted content, view_count increments, empty list states.
  - Content management: edit/delete by non-owner, delete with existing offers, soft delete visibility, missing required fields, invalid URLs, oversized thumbnails, genre count outside 1-3, onboarding incomplete producer.
  - Offers: submitting on deleted/non-public content, buyer submitting twice (pending uniqueness), expired offers actions, accept/reject on non-owner producer, invalid validity_days, currency mismatch, concurrent accept/reject race.
  - LOI: access by non-related party, missing PDF yet (503), duplicate LOI generation guard, pagination correctness.
  - Settings/Admin: password change with wrong current password, profile updates violating length limits, admin endpoints accessed by non-admin.
- **Documentation consistency check**
  - IA URLs and access matrix align with API list (docs/ia.md ↔ docs/api-spec.md). Functional IDs map to endpoints in api-spec.md; no conflicts found.
  - Response format: AGENTS.md defines `{success, data, message, pagination?}`; api-spec.md also includes optional `meta`—implement `meta` as optional.
  - Permission mapping consistent across docs/permissions.md and IA matrix; onboarding gate noted in both func-spec and AGENTS business rules.
- **Data model validation**
  - db-schema.md tables (users, booths, contents, offers, loi_documents) cover required fields/constraints from func-spec/api-spec: ArrayField tags, soft delete via `status`, offer uniqueness `(content_id, buyer_id, status='pending')`, LOI 1:1 with offer and numbering, CASCADE defaults.
  - Currency, length limits, validity_days check constraints align with specs; no missing fields detected for P0.

## Implementation Plan (ordered)
- Foundations
  - Centralize DRF settings: JWT (simplejwt), default permissions/auth classes, pagination 20/page, response envelope helper, exception handler with error codes.
  - Core app: permission classes per docs/permissions.md, onboarding middleware/decorator, status constants, soft-delete manager/queryset.
  - File upload endpoint with validation (logo/thumbnail types, sizes).
- Accounts/Auth/Onboarding
  - Extend AbstractUser with required fields (user_type, onboarding fields, company_name, country, genre_tags, booth_slug, is_onboarded).
  - Serializers/views for register/login/refresh/me/logout; enforce role immutability.
  - Onboarding producer/buyer endpoints: validation per spec, logo upload handling, booth slug generation; block if already onboarded.
  - Signals: producer creation → booth auto-create; update onboarding flags.
- Booths & Content Browsing
  - Booth model (1:1 producer) and public read endpoint (`/booths/{slug}/`) with contents listing.
  - Public content list/detail endpoints with filters/sorting, view_count increment (async safe hook).
  - Pagination standard response; soft-delete filter for public endpoints.
- Content Management (Producer)
  - CRUD endpoints under `/studio/contents/` with IsProducer+IsOwner+IsOnboarded; multipart support for create/update.
  - Delete: soft delete only, block if offers exist; return 422 code structure.
  - Offer count for producer listing summary.
- Offers
  - Buyer create endpoint with uniqueness guard and expiry calculation; email notification trigger.
  - Buyer list/detail endpoints with IsOwner filter; status filters and expires_at handling.
  - Producer list/detail endpoints; summary counts; IsOwner producer check.
  - Accept/Reject actions: state transition guards, responded_at, signal to create LOI on accept, email notifications.
  - Scheduled task for expiring offers (Celery beat hook).
- LOI
  - Model + serializer for LOI snapshot; 1:1 with offer.
  - List/detail endpoints restricted to related parties; include content/party snapshots.
  - PDF generation task & download endpoint; handle generating state with 503 code.
- Notifications
  - Email hooks for NTF-001~004 using send_mail(); template stubs and configurable sender.
- Settings
  - Profile GET/PATCH for authenticated users with role-aware fields; change-password endpoint with current password check.
- Admin
  - Admin dashboard endpoint (summary + recent lists) with IsAdmin; period filter (7d/30d).
- Testing & QA
  - Unit/DRF tests per feature: auth/onboarding, content public, producer CRUD, offers (buyer/prod flows), LOI access, settings, admin.
  - Cover edge cases: duplicate pending offer, delete with offers, unauthorized access, onboarding gate, PDF generating response, pagination metadata.
  - Add factory fixtures and test helpers; use pytest if configured (or Django test).

## Deliverables & Next Steps
- Implement per order above, committing after major modules (accounts/onboarding → contents → offers/LOI → settings/admin).
- Keep docs in sync if APIs deviate; update OpenAPI via drf-spectacular after endpoint completion.

## Page Build Plan (IA aligned, all P0 functions covered)
- **회원가입 `/join`** — AllowAny; AUTH-001~005; API: POST `/api/v1/auth/register/`; validate email duplication + password rules; post-signup redirect to onboarding by role.
- **로그인 `/login`** — AllowAny; AUTH-010; API: POST `/api/v1/auth/login/`; handle blocked inactive; store tokens, role-based redirect (permissions matrix).
- **온보딩-제작사 `/onboarding/producer`** — IsAuthenticated+IsProducer+!is_onboarded; ONB-001~005; APIs: POST `/api/v1/onboarding/producer/`, POST `/api/v1/upload/` (logo); slug collision messaging; gate other pages until onboarded.
- **온보딩-바이어 `/onboarding/buyer`** — IsAuthenticated+IsBuyer+!is_onboarded; ONB-010~011; API: POST `/api/v1/onboarding/buyer/`; ensure redirect after completion.
- **콘텐츠 브라우징 `/browse`** — AllowAny; BRW-001~006; API: GET `/api/v1/contents/` with q/genre/price filters, pagination; empty state messaging.
- **콘텐츠 상세 `/content/:contentId`** — AllowAny; CNT-001~004; API: GET `/api/v1/contents/{id}/`; show offer CTA only for authenticated buyers (can_submit_offer flag), fallback to login prompt; show booth link.
- **제작사 부스 `/booth/:slug`** — AllowAny; BTH-001~002; API: GET `/api/v1/booths/{slug}/`; list producer contents.
- **오퍼 작성 `/content/:contentId/offer` (or modal)** — IsAuthenticated+IsBuyer; OFR-001~006; APIs: GET `/api/v1/contents/{id}/` (prefill), POST `/api/v1/offers/`; handle duplicate pending offer 409 → inline alert; validity_days presets.
- **[제작사] 콘텐츠 관리 `/studio/contents`** — IsAuthenticated+IsProducer+IsOnboarded; STD-001~004; API: GET `/api/v1/studio/contents/`; actions to edit/delete with soft-delete guard and offer-blocking error display.
- **[제작사] 콘텐츠 업로드 `/studio/contents/new`** — IsAuthenticated+IsProducer+IsOnboarded; UPL-001~007; APIs: POST `/api/v1/studio/contents/`, POST `/api/v1/upload/` (thumbnail); enforce genre count, file size/type.
- **[제작사] 콘텐츠 수정 `/studio/contents/:contentId/edit`** — IsAuthenticated+IsProducer+IsOwner; UPL-001~007; APIs: GET `/api/v1/studio/contents/{id}/`, PATCH `/api/v1/studio/contents/{id}/`, DELETE `/api/v1/studio/contents/{id}/` (soft delete).
- **[제작사] 오퍼 관리 `/studio/offers`** — IsAuthenticated+IsProducer; OFR-030; API: GET `/api/v1/studio/offers/` with filters + summary; link to detail.
- **[제작사] 오퍼 상세 `/studio/offers/:offerId`** — IsAuthenticated+IsProducer+IsOwner; OFR-040~043; APIs: GET `/api/v1/studio/offers/{id}/`, POST `/api/v1/studio/offers/{id}/accept/`, POST `/api/v1/studio/offers/{id}/reject/`; show price comparison and confirmation modals.
- **[바이어] 내 오퍼 `/my/offers`** — IsAuthenticated+IsBuyer; OFR-010~011; API: GET `/api/v1/buyer/offers/`; status filter and pagination.
- **[바이어] 오퍼 상세 `/my/offers/:offerId`** — IsAuthenticated+IsBuyer+IsOwner; OFR-020~021; API: GET `/api/v1/buyer/offers/{id}/`; surface LOI link when accepted.
- **[공통] LOI 문서함 `/loi`** — IsAuthenticated (Producer/Buyer only); LOI-001~002; API: GET `/api/v1/loi/`; show counterparty and pagination.
- **[공통] LOI 상세 `/loi/:loiId`** — IsAuthenticated+IsRelatedParty; LOI-010~012; APIs: GET `/api/v1/loi/{id}/`, GET `/api/v1/loi/{id}/download/`; handle PDF generating/403 states.
- **설정 `/settings`** — IsAuthenticated; SET-001~003; APIs: GET/PATCH `/api/v1/settings/profile/`, POST `/api/v1/settings/change-password/`, POST `/api/v1/auth/logout/`; role-aware fields (producer vs buyer).
- **[관리자] 대시보드 `/admin`** — IsAuthenticated+IsAdmin; ADM-001~005; API: GET `/api/v1/admin/dashboard/`; period toggle (7d/30d) and recent lists.

## Code Architecture Conventions

### 1. 앱 구조
각 주요 도메인은 독립 앱으로 구성하며, apps/<domain>/ 형태를 따른다.

apps/
  accounts/
  content/
  offer/
  loi/
  notification/
  settings/
  adminpanel/

앱 간 import는 상위 공통 모듈(apps.common)를 제외하고 순환참조를 만들지 않는다.

### 2. 파일 구조
각 앱은 아래 구조를 기본으로 한다:

apps/<domain>/
  models.py
  serializers.py
  views/
    __init__.py
    <feature>_views.py
  services/
    <feature>_service.py
  permissions.py
  urls.py

### 3. View 원칙
- 목록: ListAPIView  
- 생성: CreateAPIView  
- 단일조회: RetrieveAPIView  
- 수정: UpdateAPIView  
- 복합동작: APIView 또는 GenericAPIView를 사용  

View 내부에서 비즈니스 로직을 작성하지 않는다 → services로 분리.

### 4. Service Layer 원칙
services/ 폴더에 “도메인 로직”을 분리한다.
- DB 트랜잭션
- 상태 전환
- 조건 검증
- 통지/후처리

View는 서비스의 입력/출력만 연결한다.

### 5. Serializer 원칙
- 입력용 Serializer(InputSerializer)와 출력용 Serializer(OutputSerializer)를 분리한다.
- ModelSerializer는 database I/O가 필요한 곳에서만 사용한다.
- Validation은 Serializer에서 담당한다.

### 6. 모델(Model) 원칙
- 모든 모델은 created_at / updated_at / is_deleted 필드를 포함한다.
- QuerySet 커스텀 로직은 managers.py를 만들어 분리한다.
- UUID primary key 또는 auto-increment 중 프로젝트 표준을 따른다.

### 7. URL & 네이밍 규칙
- URL path는 kebab-case를 사용한다 (/offer-request/)
- View class 이름은 <Feature><Action>View 형태를 사용한다.
  예: OfferRequestCreateView

### 8. 의존성 주입/Helper
공용 유틸리티는 apps/common/에 넣으며  
어느 앱에서도 import 가능하도록 한다.

### 9. DB 트랜잭션
아래 상황에서는 atomic()을 사용한다:
- 상태 변경
- 생성 + 연관 데이터 생성
- Offer/LOI처럼 "도메인 이벤트"가 있는 작업

### 10. Logging
- 중요한 도메인 이벤트는 logger.info로 기록
- 예외 발생 시 logger.error로 full traceback 기록
