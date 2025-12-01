# ShortDeal - AI Agent Guidelines

## Project Context
- **Type**: B2B Content Marketplace MVP
- **Timeline**: 18 days (12월 15일 마감)
- **Scope**: P0 기능만 (65개)
- **Users**: Producer (제작사), Buyer (바이어), Admin

## Tech Stack
- Django 4.2 + PostgreSQL 14+
- Django REST Framework (DRF)
- JWT Authentication (djangorestframework-simplejwt)
- Bootstrap 5.3 (English UI)
- Docker + docker-compose

## Database Rules
- Django ORM only (no raw SQL)
- PostgreSQL arrays: `ArrayField(CharField(max_length=50))`
- UTC timestamps
- Soft delete: `status` field
- Foreign keys: `CASCADE` default

## API Standards
- Base URL: `/api/v1/`
- JWT: `Authorization: Bearer {token}`
- Response format:
```json
  {
    "success": true,
    "data": {...},
    "message": "...",
    "pagination": {...}  // if list
  }
```
- Pagination: 20/page default
- Currency: USD default

## Permission Patterns
```python
# Import from core/permissions.py
AllowAny              # 공개
IsAuthenticated       # 로그인
IsProducer           # 제작사만
IsBuyer              # 바이어만
IsOwner              # 본인만
IsRelatedParty       # 거래 당사자
IsAdmin              # 관리자만
```

## Business Rules (Critical)
1. **Producer 가입 → Booth 자동 생성** (signal)
2. **동일 콘텐츠 pending 오퍼 1개만** (unique constraint)
3. **Offer 수락 → LOI 자동 생성** (signal)
4. **Email 알림**: Django `send_mail()`
5. **Onboarding 미완료 → 기능 차단**
6. **Soft delete**: `status='deleted'` (물리 삭제 X)

## File Structure
```
shortdeal/
├─ accounts/        # User, auth, onboarding
├─ booths/          # Producer booths
├─ contents/        # Content items
├─ offers/          # Offers
├─ loi/             # LOI documents
├─ core/            # Permissions, utils
└─ shortdeal/       # Settings
```

## Naming
- Models: `PascalCase` (User, Offer)
- Variables: `snake_case` (user_type)
- URLs: `kebab-case` (/my-offers/)
- Files: `snake_case` (offer_views.py)

## DO NOT
- ❌ P0 외 기능 추가
- ❌ Raw SQL
- ❌ 커스텀 User 모델 (AbstractUser 확장만)
- ❌ 조기 최적화
- ❌ GraphQL (REST만)

## Development Workflow

### Before Implementing Any P0 Feature

Always perform these 3 validations BEFORE writing code:

1. **Edge Case Analysis**
   - List all possible error scenarios for this feature
   - Consider: invalid inputs, state conflicts, permission issues, race conditions
   - Document edge cases that need handling

2. **Documentation Consistency Check**
   - Verify against `/docs/ia.md`: URL structure, access permissions, page flow
   - Verify against `/docs/func-spec.md`: Feature ID, input fields, validation rules, business logic
   - Verify against `/docs/api-spec.md`: API endpoints, request/response formats, status codes
   - Verify against `/docs/permissions.md`: Required permission classes, role restrictions
   - Report any conflicts or missing information between documents

3. **Data Model Validation**
   - Check `/docs/db-schema.md` matches feature requirements
   - Verify all required fields, relationships, and constraints exist
   - Confirm field types, max lengths, and validation rules align

**Only after all 3 validations pass → Start implementation**


## Quality Standards

### 1. API 동작 규칙
- 모든 API는 api-spec.md의 스키마와 완전히 일치해야 한다.
- request/response 필드는 명세서의 camelCase/snake_case 규칙을 따른다.
- Validation 실패 시 400, 인증 실패 시 401, 권한 실패 시 403을 사용한다.
- Soft-delete는 list/aggregation에서는 제외하고, detail 조회 시 404로 처리한다.

### 2. 성능 기준
- ORM은 N+1이 발생하지 않도록 select_related/prefetch_related를 기본 사용한다.
- 리스트 API는 pagination을 기본 적용한다.
- 모든 쿼리는 O(N) 이상 복잡도가 되지 않도록 한다.

### 3. 예외 처리 및 에러 포맷
- 모든 에러는 exceptions.py에 정의된 공용 Exception 클래스를 사용한다.
- API 오류 응답의 shape는 아래처럼 통일한다:
  {
    "error": { "code": "...", "message": "..." }
  }

### 4. 일관성
- Serializer, Model, API 이름은 명세서와 완전히 동일해야 한다.
- FK/ManyToMany는 db-schema.md와 일치해야 한다.
- 필드 추가/삭제 시 migration 파일을 반드시 생성한다.

### 5. 보안
- 모든 인증 API는 DRF Token/Auth 대신 JWT를 사용한다.
- 권한 체크는 permissions.md의 규칙만 따른다.
- 관리자 전용 API는 반드시 is_staff 또는 해당 Permission Class를 통해 보호한다.

### 6. 테스트 기준
- API는 최소 1개의 Integration test를 포함해야 한다.
- 비즈니스 로직이 있는 함수는 Unit test를 포함해야 한다.
- 테스트 데이터는 fixtures 또는 factory_boy를 사용한다.

### 7. 문서 및 주석
- 변경된 API는 swagger 자동 문서화 또는 api-spec.md에 반영해야 한다.
- 함수 주석은 "입력/출력/예외" 기준으로 최소 1줄 이상 작성된다.
