# **ShortDeal Database Schema Documentation**

**Version:** 1.0

**Date:** 2024-11-27

**Based on:** Information Architecture v1.0, Functional Specification v1.1

---

## **1. Overview**

### **1.1 Database Technology**

- **DBMS:** PostgreSQL 14+
- **ORM:** Django ORM
- **Character Set:** UTF-8
- **Timezone:** UTC

### **1.2 Design Principles**

```python
DESIGN_PRINCIPLES = {
    "P0 기능만": "MVP 범위 내 필수 테이블만 구현",
    "정규화 우선": "3NF 기준, 성능 필요 시 비정규화",
    "Soft Delete": "status 필드로 복구 가능하게 (public/deleted)",
    "Audit Trail": "created_at, updated_at 모든 테이블",
    "확장 가능": "Phase 2 추가 고려한 구조",
}

```

### **1.3 Entity Relationship Diagram**

![image.png](attachment:0d25c2ab-f710-4b4b-8dd4-bb7111815b87:image.png)

---

## **2. Table Specifications**

### **2.1 users (사용자)**

**목적:** 제작사, 바이어, 관리자 통합 관리

**연관 기능:**

- AUTH-001~005 (회원가입)
- ONB-001~011 (온보딩)
- IA: 역할별 접근 권한 매트릭스

### **필드 상세**

| 필드명 | 타입 | 제약 | 설명 | 비즈니스 규칙 |
| --- | --- | --- | --- | --- |
| `id` | SERIAL | PK | 자동 증가 ID |  |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | 로그인 이메일 | AUTH-003: 실시간 중복 검증 |
| `password` | VARCHAR(255) | NOT NULL | 해시된 비밀번호 | Django `pbkdf2_sha256` |
| `name` | VARCHAR(100) | NOT NULL | 사용자 이름 | AUTH-002: 2-50자 |
| `user_type` | VARCHAR(20) | NOT NULL | 역할 구분 | 'producer', 'buyer', 'admin' |
| `is_onboarded` | BOOLEAN | DEFAULT FALSE | 온보딩 완료 여부 | 미완료 시 다른 기능 제한 |
| `company_name` | VARCHAR(200) |  | 회사명 | ONB-001, ONB-010: 2-100자 |
| `logo_url` | VARCHAR(500) |  | 로고 이미지 URL | ONB-002: S3 업로드 경로 |
| `country` | VARCHAR(100) |  | 국가 | ONB-003, ONB-011: ISO 국가명 |
| `genre_tags` | VARCHAR(50)[] |  | 장르 태그 배열 | ONB-004: 제작사만, 최대 3개 |
| `booth_slug` | VARCHAR(100) | UNIQUE | 부스 URL slug | ONB-005: 회사명 기반 자동생성 |
| `is_active` | BOOLEAN | DEFAULT TRUE | 계정 활성화 | 관리자가 비활성화 가능 |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 가입일 |  |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | 수정일 | Django signal로 자동 업데이트 |
| `last_login` | TIMESTAMP |  | 마지막 로그인 | Django 기본 제공 |

### **인덱스**

```sql
INDEX idx_user_type ON users(user_type);          -- 역할별 조회
INDEX idx_email ON users(email);                  -- 로그인 성능
INDEX idx_booth_slug ON users(booth_slug);        -- 부스 URL 조회

```

### **비즈니스 규칙**

1. **역할 고정**: 가입 후 `user_type` 변경 불가 (AUTH-001)
2. **온보딩 강제**: `is_onboarded=FALSE`이면 온보딩 페이지로 리다이렉트
3. **부스 자동 생성**: 제작사 가입 시 `booth_slug` 자동 생성, 중복 시 숫자 suffix
4. **장르 태그**: 제작사만 입력, 바이어는 NULL

### **Django Model 예시**

```python
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('producer', 'Producer'),
        ('buyer', 'Buyer'),
        ('admin', 'Admin'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    is_onboarded = models.BooleanField(default=False)
    company_name = models.CharField(max_length=200, blank=True)
    # ... (실제 구현 시 ArrayField 사용)

```

---

### **2.2 booths (부스)**

**목적:** 제작사의 콘텐츠 진열 공간 (BTH-001~002)

**연관 기능:**

- IA: 페이지 #7 "제작사 부스 (공개)", URL `/booth/:slug`
- ONB-005: 부스 URL 자동 생성

### **필드 상세**

| 필드명 | 타입 | 제약 | 설명 | 비즈니스 규칙 |
| --- | --- | --- | --- | --- |
| `id` | SERIAL | PK | 자동 증가 ID |  |
| `producer_id` | INTEGER | FK→users(id), UNIQUE, NOT NULL | 제작사 | 1명당 1개 부스 |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL | URL 친화적 slug | SEO 최적화 |
| `title` | VARCHAR(200) | NOT NULL | 부스명 (=회사명) | BTH-001 |
| `description` | TEXT |  | 부스 설명 | 추후 확장용 |
| `view_count` | INTEGER | DEFAULT 0 | 조회수 | 통계용 |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 생성일 | 회원가입 시각 |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | 수정일 |  |

### **관계**

```
users(producer) 1 ---- 1 booths
booths 1 ---- N contents

```

### **비즈니스 규칙**

1. **자동 생성**: 제작사 가입 시 Django signal로 자동 생성
2. **1:1 관계**: `producer_id` UNIQUE 제약으로 1명당 1개 보장
3. **삭제 정책**: 제작사 탈퇴 시 CASCADE (부스도 삭제)

### **생성 로직 (Django Signal)**

```python
@receiver(post_save, sender=User)
def create_booth_for_producer(sender, instance, created, **kwargs):
    if created and instance.user_type == 'producer':
        slug = slugify(instance.company_name)
        # 중복 처리
        if Booth.objects.filter(slug=slug).exists():
            slug = f"{slug}-{instance.id}"

        Booth.objects.create(
            producer=instance,
            slug=slug,
            title=instance.company_name
        )

```

---

### **2.3 contents (콘텐츠)**

**목적:** 판매 가능한 콘텐츠 아이템

**연관 기능:**

- BRW-001~006 (브라우징)
- CNT-001~004 (상세)
- UPL-001~007 (업로드/수정)
- STD-001~004 (관리)

### **필드 상세**

| 필드명 | 타입 | 제약 | 설명 | 비즈니스 규칙 |
| --- | --- | --- | --- | --- |
| `id` | SERIAL | PK | 자동 증가 ID |  |
| `booth_id` | INTEGER | FK→booths(id), NOT NULL | 소속 부스 | 부스 삭제 시 CASCADE |
| `producer_id` | INTEGER | FK→users(id), NOT NULL | 제작사 | 비정규화 (쿼리 성능) |
| `title` | VARCHAR(200) | NOT NULL | 콘텐츠 제목 | UPL-001: 2-200자 |
| `thumbnail_url` | VARCHAR(500) | NOT NULL | 썸네일 이미지 | UPL-002: 16:9 권장 |
| `synopsis` | TEXT | NOT NULL | 시놉시스 | UPL-003: 최대 2000자 |
| `content_link` | VARCHAR(500) | NOT NULL | 외부 콘텐츠 링크 | UPL-005: URL 검증 |
| `target_price` | DECIMAL(12,2) | NOT NULL | 희망가 | UPL-004: >0 |
| `currency` | VARCHAR(3) | DEFAULT 'USD' | 통화 | USD/KRW/EUR |
| `genre_tags` | VARCHAR(50)[] |  | 장르 태그 배열 | UPL-006: 1-3개 |
| `status` | VARCHAR(20) | DEFAULT 'public' | 공개 상태 | 'public', 'deleted' |
| `view_count` | INTEGER | DEFAULT 0 | 조회수 |  |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 등록일 |  |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | 수정일 |  |

### **인덱스**

```sql
INDEX idx_booth ON contents(booth_id);              -- 부스별 콘텐츠 조회
INDEX idx_producer ON contents(producer_id);        -- 제작사별 조회
INDEX idx_status ON contents(status);               -- 공개 콘텐츠 필터
GIN INDEX idx_search ON contents USING gin(        -- 전체 텍스트 검색
    to_tsvector('english', title || ' ' || synopsis)
);

```

### **비즈니스 규칙**

1. **비정규화**: `producer_id`는 `booth_id`로 조인 가능하지만 쿼리 성능을 위해 중복 저장
2. **검색 최적화**: BRW-002 키워드 검색을 위한 GIN 인덱스
3. **Soft Delete**: `status='deleted'`로 처리, 물리 삭제 안 함
4. **삭제 제한**: STD-004에서 오퍼가 있으면 삭제 불가 (애플리케이션 레벨 검증)

### **장르 태그 저장 (PostgreSQL)**

```python
# Django Model
genre_tags = ArrayField(
    models.CharField(max_length=50),
    size=3,
    help_text="1-3 genre tags"
)

# 저장 예시
content.genre_tags = ['Drama', 'Romance', 'Comedy']

```

---

### **2.4 offers (오퍼)**

**목적:** 바이어의 구매 제안

**연관 기능:**

- OFR-001~043 (오퍼 작성, 관리, 응답)

### **필드 상세**

| 필드명 | 타입 | 제약 | 설명 | 비즈니스 규칙 |
| --- | --- | --- | --- | --- |
| `id` | SERIAL | PK | 자동 증가 ID |  |
| `content_id` | INTEGER | FK→contents(id), NOT NULL | 대상 콘텐츠 |  |
| `buyer_id` | INTEGER | FK→users(id), NOT NULL | 오퍼 제출자 |  |
| `producer_id` | INTEGER | FK→users(id), NOT NULL | 오퍼 수신자 | 비정규화 |
| `offer_price` | DECIMAL(12,2) | NOT NULL | 제안가 | OFR-001: >0 |
| `currency` | VARCHAR(3) | DEFAULT 'USD' | 통화 |  |
| `message` | TEXT |  | 바이어 메모 | OFR-002: 최대 500자 |
| `validity_days` | INTEGER | NOT NULL | 유효기간 (일) | OFR-003: 7, 14, 30만 허용 |
| `expires_at` | TIMESTAMP | NOT NULL | 만료 시각 | 자동 계산 |
| `status` | VARCHAR(20) | DEFAULT 'pending' | 오퍼 상태 | 'pending', 'accepted', 'rejected', 'expired' |
| `responded_at` | TIMESTAMP |  | 응답 시각 | accept/reject 시각 |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 제출일 |  |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | 수정일 |  |

### **제약 조건**

```sql
-- OFR-006: 중복 오퍼 방지
UNIQUE (content_id, buyer_id) WHERE status = 'pending';

-- 유효기간 검증
CHECK (validity_days IN (7, 14, 30));

-- 상태 검증
CHECK (status IN ('pending', 'accepted', 'rejected', 'expired'));

```

### **인덱스**

```sql
INDEX idx_content ON offers(content_id);
INDEX idx_buyer ON offers(buyer_id);
INDEX idx_producer ON offers(producer_id);
INDEX idx_status ON offers(status);
INDEX idx_expires ON offers(expires_at);              -- 만료 처리용

```

### **비즈니스 규칙**

1. **중복 방지**: OFR-006에 따라 동일 바이어가 동일 콘텐츠에 pending 오퍼 1개만 가능 (다른 바이어는 별도 오퍼 제출 가능)
2. **자동 만료**: Celery 스케줄러로 `expires_at` 지난 pending 오퍼를 'expired'로 변경
3. **LOI 자동 생성**: OFR-042에서 수락 시 Django signal로 LOI 생성
4. **상태 전이**:
    
    ```
    pending → accepted → LOI 생성pending → rejectedpending → expired (자동)
    
    ```
    

### **Celery Task 예시**

```python
@periodic_task(run_every=timedelta(hours=1))
def expire_old_offers():
    Offer.objects.filter(
        status='pending',
        expires_at__lt=timezone.now()
    ).update(status='expired')

```

---

### **2.5 loi_documents (의향서)**

**목적:** 오퍼 수락 시 생성되는 법적 문서

**연관 기능:**

- LOI-001~012 (문서함, 상세, 다운로드)

### **필드 상세**

| 필드명 | 타입 | 제약 | 설명 | 비즈니스 규칙 |
| --- | --- | --- | --- | --- |
| `id` | SERIAL | PK | 자동 증가 ID |  |
| `offer_id` | INTEGER | FK→offers(id), UNIQUE, NOT NULL | 원본 오퍼 | 1:1 관계 |
| `content_id` | INTEGER | FK→contents(id), NOT NULL | 콘텐츠 | 비정규화 |
| `buyer_id` | INTEGER | FK→users(id), NOT NULL | 바이어 | 비정규화 |
| `producer_id` | INTEGER | FK→users(id), NOT NULL | 제작사 | 비정규화 |
| `document_number` | VARCHAR(50) | UNIQUE, NOT NULL | LOI 번호 | 'LOI-2024-00001' 형식 |
| `producer_company` | VARCHAR(200) | NOT NULL | 제작사명 (스냅샷) | 변경 대비 |
| `producer_country` | VARCHAR(100) |  | 제작사 국가 |  |
| `buyer_company` | VARCHAR(200) | NOT NULL | 바이어사명 (스냅샷) |  |
| `buyer_country` | VARCHAR(100) |  | 바이어 국가 |  |
| `content_title` | VARCHAR(200) | NOT NULL | 콘텐츠 제목 (스냅샷) |  |
| `agreed_price` | DECIMAL(12,2) | NOT NULL | 합의가 | `offer.offer_price` 복사 |
| `currency` | VARCHAR(3) | DEFAULT 'USD' | 통화 |  |
| `pdf_url` | VARCHAR(500) |  | PDF 파일 URL | LOI-011: S3 업로드 |
| `generated_at` | TIMESTAMP | DEFAULT NOW() | 생성일 |  |

### **인덱스**

```sql
INDEX idx_offer ON loi_documents(offer_id);
INDEX idx_buyer ON loi_documents(buyer_id);
INDEX idx_producer ON loi_documents(producer_id);
INDEX idx_document_number ON loi_documents(document_number);

```

### **비즈니스 규칙**

1. **자동 생성**: 오퍼 수락 시 Django signal로 자동 생성
2. **스냅샷 방식**: 회사명, 콘텐츠 제목 등을 복사 저장 (원본 변경 영향 없음)
3. **고유 번호**: LOI-012 형식, 시퀀스 자동 증가
4. **PDF 생성**: 백그라운드 Celery task로 PDF 생성 후 S3 업로드

### **LOI 생성 Signal**

```python
@receiver(post_save, sender=Offer)
def create_loi_on_acceptance(sender, instance, **kwargs):
    if instance.status == 'accepted' and not hasattr(instance, 'loi'):
        # 최신 LOI 번호 조회
        latest = LOIDocument.objects.order_by('-id').first()
        next_num = (latest.id + 1) if latest else 1
        doc_number = f"LOI-{timezone.now().year}-{next_num:05d}"

        LOIDocument.objects.create(
            offer=instance,
            content=instance.content,
            buyer=instance.buyer,
            producer=instance.producer,
            document_number=doc_number,
            producer_company=instance.producer.company_name,
            producer_country=instance.producer.country,
            buyer_company=instance.buyer.company_name,
            buyer_country=instance.buyer.country,
            content_title=instance.content.title,
            agreed_price=instance.offer_price,
            currency=instance.currency,
        )

        # 비동기 PDF 생성
        generate_loi_pdf.delay(instance.id)

```

---

## **3. Relationships Summary**

```
users (producer)  1 ──── 1  booths
users (producer)  1 ──── N  contents
booths            1 ──── N  contents
users (buyer)     1 ──── N  offers
contents          1 ──── N  offers
users (producer)  1 ──── N  offers (received)
offers            1 ──── 1  loi_documents

```

---

## **4. Data Types & Conventions**

### **4.1 Primary Keys**

- 모든 테이블: `SERIAL` (자동 증가)
- UUID 사용 안 함 (오버헤드)

### **4.2 Timestamps**

- `created_at`: 생성 시각 (불변)
- `updated_at`: 수정 시각 (Django signal 자동 업데이트)
- 모두 UTC 기준

### **4.3 Soft Delete**

- `deleted_at` 대신 `status` 필드 사용
- `contents.status`: 'public', 'deleted'
- 물리 삭제는 관리자 수동 작업

### **4.4 Money Fields**

- `DECIMAL(12,2)`: 최대 9,999,999,999.99
- 통화: ISO 4217 코드 (USD, KRW, EUR)

### **4.5 Arrays (PostgreSQL)**

- `genre_tags`: `VARCHAR(50)[]` (PostgreSQL array)
- Django: `ArrayField` 사용

---

## **5. Indexes Strategy**

### **5.1 Primary Indexes**

모든 테이블의 PK에 자동 생성

### **5.2 Foreign Key Indexes**

모든 FK에 인덱스 생성 (JOIN 성능)

### **5.3 Business Logic Indexes**

```sql
-- 검색 성능
contents.idx_search (GIN)

-- 역할별 필터
users.idx_user_type

-- 상태별 조회
contents.idx_status
offers.idx_status

-- 만료 처리
offers.idx_expires

```

---

## **6. Migration Plan**

### **6.1 초기 마이그레이션 순서**

```python
MIGRATION_ORDER = [
    "0001_users",           # 사용자 테이블
    "0002_booths",          # 부스 (users FK)
    "0003_contents",        # 콘텐츠 (booths, users FK)
    "0004_offers",          # 오퍼 (contents, users FK)
    "0005_loi_documents",   # LOI (offers FK)
]

```

### **6.2 Phase 2 예정**

- `notifications`: 인앱 알림
- `activity_logs`: 감사 추적
- `messages`: 제작사-바이어 메시징

---

## **7. Backup & Recovery**

### **7.1 백업 전략**

- **Daily**: 전체 DB 덤프 (pg_dump)
- **Hourly**: WAL 아카이빙
- **Retention**: 30일

### **7.2 복구 시나리오**

- Soft delete로 복구 가능
- Point-in-time recovery (PITR)

---

## **8. Security Considerations**

### **8.1 민감 정보**

- `password`: Django PBKDF2 해싱
- 개인정보 암호화 (Phase 2)

### **8.2 접근 제어**

- Row-level security (PostgreSQL RLS) 고려
- Django ORM 쿼리셋 필터링으로 구현

---

## **9. Performance Tuning**

### **9.1 비정규화**

- `contents.producer_id`: 조인 회피
- `offers.producer_id`: 조인 회피
- `loi_documents.*`: 스냅샷 방식

### **9.2 인덱스 모니터링**

```sql
-- 사용되지 않는 인덱스 확인
SELECT * FROM pg_stat_user_indexes
WHERE idx_scan = 0;

```

---

## **10. Known Limitations**

### **10.1 MVP 제약**

- 서명 기능 없음 (LOI)
- 파일 버전 관리 없음
- 다중 통화 환율 변환 없음

### **10.2 스케일링 고려사항**

- 콘텐츠 10만 개 이상 시 파티셔닝 고려
- 오퍼 테이블 시계열 파티셔닝

---

## **11. References**

- [Information Architecture v1.0](https://claude.ai/chat/%EB%A7%81%ED%81%AC)
- [Functional Specification v1.1](https://claude.ai/chat/%EB%A7%81%ED%81%AC)
- [PostgreSQL Array Types](https://www.postgresql.org/docs/current/arrays.html)
- [Django Model Field Reference](https://docs.djangoproject.com/en/4.2/ref/models/fields/)

---

## **Appendix A: SQL Scripts**

### **A.1 전체 스키마 생성**

```json
// ShortDeal MVP Database Schema

Table users {
  id serial [pk, increment]
  email varchar(255) [unique, not null]
  password varchar(255) [not null]
  name varchar(100) [not null]
  user_type varchar(20) [not null, note: 'producer/buyer/admin']
  is_onboarded boolean [default: false]
  company_name varchar(200)
  logo_url varchar(500)
  country varchar(100)
  genre_tags varchar(50)[] [note: 'PostgreSQL array']
  booth_slug varchar(100) [unique]
  is_active boolean [default: true]
  created_at timestamp [default: `now()`]
  updated_at timestamp [default: `now()`]
  last_login timestamp
  
  indexes {
    user_type
    email
    booth_slug
  }
}

Table booths {
  id serial [pk, increment]
  producer_id integer [unique, not null, ref: > users.id]
  slug varchar(100) [unique, not null]
  title varchar(200) [not null]
  description text
  view_count integer [default: 0]
  created_at timestamp [default: `now()`]
  updated_at timestamp [default: `now()`]
  
  indexes {
    producer_id
    slug
  }
}

Table contents {
  id serial [pk, increment]
  booth_id integer [not null, ref: > booths.id]
  producer_id integer [not null, ref: > users.id]
  title varchar(200) [not null]
  thumbnail_url varchar(500) [not null]
  synopsis text [not null]
  content_link varchar(500) [not null]
  target_price decimal(12,2) [not null]
  currency varchar(3) [default: 'USD']
  genre_tags varchar(50)[]
  status varchar(20) [default: 'public', note: 'public/deleted']
  view_count integer [default: 0]
  created_at timestamp [default: `now()`]
  updated_at timestamp [default: `now()`]
  
  indexes {
    booth_id
    producer_id
    status
    (title, synopsis) [type: fulltext]
  }
}

Table offers {
  id serial [pk, increment]
  content_id integer [not null, ref: > contents.id]
  buyer_id integer [not null, ref: > users.id]
  producer_id integer [not null, ref: > users.id]
  offer_price decimal(12,2) [not null]
  currency varchar(3) [default: 'USD']
  message text
  validity_days integer [not null, note: '7/14/30']
  expires_at timestamp [not null]
  status varchar(20) [default: 'pending', note: 'pending/accepted/rejected/expired']
  responded_at timestamp
  created_at timestamp [default: `now()`]
  updated_at timestamp [default: `now()`]
  
  indexes {
    content_id
    buyer_id
    producer_id
    status
    expires_at
    (content_id, buyer_id, status) [unique, note: 'Prevent duplicate pending offers']
  }
}

Table loi_documents {
  id serial [pk, increment]
  offer_id integer [unique, not null, ref: - offers.id]
  content_id integer [not null, ref: > contents.id]
  buyer_id integer [not null, ref: > users.id]
  producer_id integer [not null, ref: > users.id]
  document_number varchar(50) [unique, not null, note: 'LOI-2024-00001']
  producer_company varchar(200) [not null]
  producer_country varchar(100)
  buyer_company varchar(200) [not null]
  buyer_country varchar(100)
  content_title varchar(200) [not null]
  agreed_price decimal(12,2) [not null]
  currency varchar(3) [default: 'USD']
  pdf_url varchar(500)
  generated_at timestamp [default: `now()`]
  
  indexes {
    offer_id
    buyer_id
    producer_id
    document_number
  }
}

// Relationships Summary
// users 1 --o 1 booths (producer has one booth)
// booths 1 --o N contents (booth contains many contents)
// users 1 --o N contents (producer creates many contents)
// contents 1 --o N offers (content receives many offers)
// users 1 --o N offers (buyer submits many offers)
// users 1 --o N offers (producer receives many offers)
// offers 1 --o 1 loi_documents (offer generates one LOI)
```

### **A.2 초기 데이터**

```sql
-- 관리자 계정
INSERT INTO users (email, user_type, is_onboarded)
VALUES ('admin@shortdeal.com', 'admin', true);

```

---

## **변경 이력**

| 버전 | 날짜 | 변경 내용 |
| --- | --- | --- |
| 1.0 | 2024-11-27 | 초안 작성 (5개 테이블) |