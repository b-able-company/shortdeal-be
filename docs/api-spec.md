# **ShortDeal API Structure Documentation**

**Version:** 1.0

**Date:** 2024-11-27

**Based on:** Database Schema v1.0, Functional Specification v1.1

---

## **1. Overview**

### **1.1 API Architecture Decision**

```python
API_CHOICE = {
    "선택": "REST API",
    "이유": [
        "MVP 18일 일정 - REST가 더 빠름",
        "Django REST Framework 성숙도",
        "글로벌 바이어 - REST가 더 보편적",
        "캐싱 전략 단순",
    ],
    "GraphQL": "Phase 2에서 고려 (복잡한 쿼리 필요 시)",
}
```

### **1.2 Technology Stack**

- **Framework:** Django REST Framework (DRF) 3.14+
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Serialization:** DRF Serializers
- **API Documentation:** drf-spectacular (OpenAPI 3.0)
- **Rate Limiting:** django-ratelimit
- **CORS:** django-cors-headers

### **1.3 Base URL**
```
Development:  http://localhost:8000/api/v1
Production:   https://api.shortdeal.com/v1
```

### **1.4 Versioning Strategy**

- URL 경로 기반: `/api/v1/`, `/api/v2/`
- 하위 호환성 유지
- Deprecation 최소 3개월 전 공지

---

## **2. Authentication & Authorization**

### **2.1 JWT Token Flow**
```
1. POST /api/v1/auth/login/
   → Response: { access_token, refresh_token }

2. 이후 모든 요청 Header:
   Authorization: Bearer {access_token}

3. Token 만료 시:
   POST /api/v1/auth/refresh/
   Body: { refresh: "{refresh_token}" }
   → Response: { access: "{new_access_token}" }
```

**2.2 Token Lifetime**

```python
TOKEN_SETTINGS = {
    "ACCESS_TOKEN_LIFETIME": "15 minutes",
    "REFRESH_TOKEN_LIFETIME": "7 days",
    "ROTATE_REFRESH_TOKENS": True,
}
```

**2.3 Permission Classes**

```python
PERMISSIONS = {
    "IsAuthenticated": "로그인 필수",
    "IsProducer": "제작사만",
    "IsBuyer": "바이어만",
    "IsOwner": "본인 데이터만",
    "IsAdmin": "관리자만",
}
```

---

## **3. API Endpoints Structure**

### **3.1 Endpoint Naming Conventions**

```python
CONVENTIONS = {
    "리소스": "복수형 명사 (users, contents, offers)",
    "URL": "소문자, 하이픈 구분 (kebab-case)",
    "메서드": "RESTful 표준 (GET, POST, PUT, PATCH, DELETE)",
    "필터": "쿼리 파라미터 (?status=pending&page=2)",
}
```

### **3.2 Standard Response Format**

### **Success Response**

```json
**{
  "success": true,
  "data": { /* 실제 데이터 */ },
  "message": "Operation completed successfully",
  "meta": {
    "timestamp": "2024-11-27T10:30:00Z",
    "request_id": "uuid-here"
  }
}**
```

**Error Response**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": ["This field is required."],
      "price": ["Ensure this value is greater than 0."]
    }
  },
  "meta": {
    "timestamp": "2024-11-27T10:30:00Z",
    "request_id": "uuid-here"
  }
}
```

**Pagination Response**

```json
{
  "success": true,
  "data": [/* 아이템 배열 */],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false,
    "next": "/api/v1/contents/?page=2",
    "previous": null
  }
}
```

### **3.3 HTTP Status Codes**

| Code | 의미 | 사용 예 |
| --- | --- | --- |
| 200 | OK | 성공적인 GET, PUT, PATCH |
| 201 | Created | 성공적인 POST (생성) |
| 204 | No Content | 성공적인 DELETE |
| 400 | Bad Request | 유효성 검증 실패 |
| 401 | Unauthorized | 인증 실패 (토큰 없음/만료) |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 409 | Conflict | 중복 데이터 (OFR-006) |
| 422 | Unprocessable Entity | 비즈니스 규칙 위반 |
| 429 | Too Many Requests | Rate limit 초과 |
| 500 | Internal Server Error | 서버 에러 |

---

## **4. Detailed API Endpoints**

### **4.1 Authentication APIs**

### **POST /api/v1/auth/register/**

회원가입 (AUTH-001~005)

**Request:**

```json
{
  "email": "producer@example.com",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123",
  "name": "John Doe",
  "user_type": "producer"  // "producer" | "buyer"
}

```

**Validation Rules:**

- `email`: 유효한 이메일 형식, 중복 불가
- `password`: 최소 8자, 영문+숫자 조합
- `password_confirm`: password와 일치
- `name`: 2-50자
- `user_type`: "producer" 또는 "buyer"만 허용

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "email": "producer@example.com",
      "name": "John Doe",
      "user_type": "producer",
      "is_onboarded": false
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbG...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbG..."
    }
  },
  "message": "Registration successful. Please complete onboarding."
}

```

**Errors:**

- 400: 이메일 중복, 유효성 검증 실패
- 500: 서버 오류

---

### **POST /api/v1/auth/login/**

로그인 (AUTH-010)

**Request:**

```json
{
  "email": "producer@example.com",
  "password": "SecurePass123"
}

```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "email": "producer@example.com",
      "name": "John Doe",
      "user_type": "producer",
      "is_onboarded": true,
      "company_name": "MediaCraft Studios",
      "booth_slug": "mediacraft-studios"
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbG...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbG..."
    }
  },
  "message": "Login successful"
}

```

**Errors:**

- 401: 이메일 또는 비밀번호 오류
- 403: 계정 비활성화 (is_active=False)

---

### **POST /api/v1/auth/refresh/**

토큰 갱신

**Request:**

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbG..."
}

```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbG...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbG..."  // rotate된 새 refresh token
  }
}

```

---

### **GET /api/v1/auth/me/**

현재 사용자 정보

**Headers:**

```
Authorization: Bearer {access_token}

```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "producer@example.com",
    "name": "John Doe",
    "user_type": "producer",
    "is_onboarded": true,
    "company_name": "MediaCraft Studios",
    "logo_url": "<https://s3>.../logo.png",
    "country": "United States",
    "genre_tags": ["Drama", "Reality"],
    "booth_slug": "mediacraft-studios",
    "created_at": "2024-11-01T10:00:00Z"
  }
}

```

---

### **4.2 Onboarding APIs**

### **POST /api/v1/onboarding/producer/**

제작사 온보딩 (ONB-001~005)

**Permission:** IsAuthenticated, IsProducer, is_onboarded=False

**Request (multipart/form-data):**

```
company_name: "MediaCraft Studios"
logo: [File]
country: "United States"
genre_tags: ["Drama", "Reality", "Documentary"]  // 최대 3개

```

**Validation:**

- `company_name`: 2-100자, 필수
- `logo`: JPG/PNG, 최대 2MB, 1:1 비율 권장
- `country`: ISO 국가명
- `genre_tags`: 1-3개, 미리 정의된 목록에서만

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "is_onboarded": true,
      "company_name": "MediaCraft Studios",
      "logo_url": "<https://s3>.../logo.png",
      "country": "United States",
      "genre_tags": ["Drama", "Reality", "Documentary"],
      "booth_slug": "mediacraft-studios"
    },
    "booth": {
      "id": 1,
      "slug": "mediacraft-studios",
      "title": "MediaCraft Studios",
      "url": "/booth/mediacraft-studios"
    }
  },
  "message": "Onboarding completed successfully"
}

```

**Business Logic:**

- 부스 자동 생성 (Django signal)
- `booth_slug` = slugify(company_name), 중복 시 숫자 suffix
- `is_onboarded` = True로 변경

---

### **POST /api/v1/onboarding/buyer/**

바이어 온보딩 (ONB-010~011)

**Permission:** IsAuthenticated, IsBuyer, is_onboarded=False

**Request:**

```json
{
  "company_name": "StreamMax International",
  "country": "Canada"
}

```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 2,
      "is_onboarded": true,
      "company_name": "StreamMax International",
      "country": "Canada"
    }
  },
  "message": "Onboarding completed successfully"
}

```

---

### **4.3 Content Browsing APIs**

### **GET /api/v1/contents/**

콘텐츠 목록 조회 (BRW-001~006)

**Permission:** AllowAny (공개)

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 설명 | 예시 |
| --- | --- | --- | --- | --- |
| `q` | string | ❌ | 검색 키워드 (제목, 시놉시스, 제작사명) | `?q=drama` |
| `genre` | string[] | ❌ | 장르 필터 (다중 선택) | `?genre=Drama&genre=Romance` |
| `price_min` | decimal | ❌ | 최소 희망가 | `?price_min=1000` |
| `price_max` | decimal | ❌ | 최대 희망가 | `?price_max=5000` |
| `currency` | string | ❌ | 통화 필터 | `?currency=USD` |
| `sort` | string | ❌ | 정렬 기준 | `?sort=-created_at` (최신순) |
| `page` | integer | ❌ | 페이지 번호 (기본: 1) | `?page=2` |
| `page_size` | integer | ❌ | 페이지 크기 (기본: 20, 최대: 100) | `?page_size=50` |

**Sort Options:**

- `created_at`: 등록일 오름차순
- `created_at`: 등록일 내림차순 (최신순)
- `target_price`: 가격 오름차순
- `target_price`: 가격 내림차순
- `view_count`: 조회수 오름차순
- `view_count`: 조회수 내림차순 (인기순)

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Corporate Training Video Series",
      "poster_url": "<https://s3>.../poster.jpg",
      "rating": "all",
      "synopsis": "10-episode professional training...",
      "target_price": 5000.00,
      "currency": "USD",
      "genre_tags": ["Education", "Business"],
      "status": "public",
      "view_count": 245,
      "created_at": "2024-11-15T10:00:00Z",
      "producer": {
        "id": 1,
        "company_name": "MediaCraft Studios",
        "booth_slug": "mediacraft-studios",
        "logo_url": "<https://s3>.../logo.png"
      },
      "url": "/content/1"
    },
    // ... 19 more items
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}

```

**Empty State (200 OK):**

```json
{
  "success": true,
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 0,
    "total_pages": 0,
    "has_next": false,
    "has_previous": false
  },
  "message": "No content found matching your criteria"
}

```

---

### **GET /api/v1/contents/{id}/**

콘텐츠 상세 조회 (CNT-001~004)

**Permission:** AllowAny (공개)

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Corporate Training Video Series",
    "poster_url": "<https://s3>.../poster.jpg",
    "rating": "all",
    "synopsis": "10-episode professional training content for enterprise clients. Each episode covers essential workplace skills including communication, leadership, and teamwork...",
    "content_link": "<https://vimeo.com/12345>",
    "screener_url": "<https://internal.shortdeal.com/screener/1>",
    "release_target": "2025-03-01",
    "target_price": 5000.00,
    "currency": "USD",
    "genre_tags": ["Education", "Business"],
    "status": "public",
    "view_count": 246,  // 조회 시 자동 +1
    "created_at": "2024-11-15T10:00:00Z",
    "updated_at": "2024-11-15T10:00:00Z",
    "producer": {
      "id": 1,
      "company_name": "MediaCraft Studios",
      "logo_url": "<https://s3>.../logo.png",
      "country": "United States",
      "booth_slug": "mediacraft-studios",
      "booth_url": "/booth/mediacraft-studios"
    },
    "booth": {
      "id": 1,
      "slug": "mediacraft-studios",
      "title": "MediaCraft Studios"
    },
    "can_submit_offer": true  // 바이어 로그인 시에만 true
  }
}

```

**Errors:**

- 404: 콘텐츠 없음 또는 삭제됨 (status='deleted')

**Side Effect:**

- `view_count` +1 증가 (비동기 처리 권장)

---

### **GET /api/v1/booths/{slug}/**

제작사 부스 조회 (BTH-001~002)

**Permission:** AllowAny (공개)

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "booth": {
      "id": 1,
      "slug": "mediacraft-studios",
      "title": "MediaCraft Studios",
      "description": "",
      "view_count": 1520,
      "created_at": "2024-11-01T10:00:00Z"
    },
    "producer": {
      "id": 1,
      "company_name": "MediaCraft Studios",
      "logo_url": "<https://s3>.../logo.png",
      "country": "United States",
      "genre_tags": ["Drama", "Reality", "Documentary"]
    },
    "contents": [
      {
        "id": 1,
        "title": "Corporate Training Video Series",
        "poster_url": "<https://s3>.../thumb.jpg",
        "target_price": 5000.00,
        "currency": "USD",
        "genre_tags": ["Education", "Business"],
        "view_count": 246,
        "url": "/content/1"
      },
      // ... more contents
    ],
    "contents_count": 8
  }
}

```

**Errors:**

- 404: 부스 없음

---

### **4.4 Content Management APIs (Producer)**

### **GET /api/v1/studio/contents/**

내 콘텐츠 목록 (STD-001)

**Permission:** IsAuthenticated, IsProducer

**Query Parameters:**

- `status`: 'public' | 'deleted'
- `page`, `page_size`

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Corporate Training Video Series",
      "poster_url": "<https://s3>.../thumb.jpg",
      "target_price": 5000.00,
      "currency": "USD",
      "genre_tags": ["Education", "Business"],
      "status": "public",
      "view_count": 246,
      "offer_count": 3,  // 받은 오퍼 수
      "created_at": "2024-11-15T10:00:00Z",
      "actions": {
        "edit": "/studio/contents/1/edit",
        "delete": "/studio/contents/1/delete"
      }
    }
  ],
  "pagination": { /* ... */ }
}

```

---

### **POST /api/v1/studio/contents/**

콘텐츠 업로드 (UPL-001~007)

**Permission:** IsAuthenticated, IsProducer, is_onboarded=True

**Request (multipart/form-data):**

```
title: "New Content Title"
poster: [File]  // Optional
rating: "15"  // all/12/15/19
synopsis: "Detailed description..."
content_link: "<https://vimeo.com/12345>"
screener_url: "<https://internal.shortdeal.com/screener/12345>"  // Optional
release_target: "2025-06-15"  // Optional
target_price: 5000.00
currency: "USD"
genre_tags: ["Drama", "Romance"]  // 1-3개

```

**Validation:**

- `title`: 2-200자, 필수
- `poster`: JPG/PNG, 최대 5MB, 세로형 권장, 선택
- `rating`: all/12/15/19 중 선택, 필수
- `synopsis`: 최대 2000자, 필수
- `content_link`: 유효한 URL, 필수 (외부 링크)
- `screener_url`: 유효한 URL, 선택 (내부 워터마크 스크리너)
- `release_target`: YYYY-MM-DD 형식, 선택
- `target_price`: >0, 필수
- `currency`: USD/KRW/EUR, 필수
- `genre_tags`: 1-3개, 미리 정의된 목록, 필수

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": 10,
    "title": "New Content Title",
    "poster_url": "<https://s3>.../new-poster.jpg",
    "rating": "15",
    "synopsis": "Detailed description...",
    "content_link": "<https://vimeo.com/12345>",
    "screener_url": "<https://internal.shortdeal.com/screener/12345>",
    "release_target": "2025-06-15",
    "target_price": 5000.00,
    "currency": "USD",
    "genre_tags": ["Drama", "Romance"],
    "status": "public",
    "created_at": "2024-11-27T10:30:00Z",
    "url": "/content/10"
  },
  "message": "Content uploaded successfully"
}

```

**Business Logic:**

- `booth_id`: 현재 사용자의 부스 자동 할당
- `producer_id`: 현재 사용자 자동 할당
- `status`: 'public'으로 자동 설정

**Errors:**

- 400: 유효성 검증 실패
- 403: 온보딩 미완료

---

### **GET /api/v1/studio/contents/{id}/**

내 콘텐츠 상세 (편집용)

**Permission:** IsAuthenticated, IsProducer, IsOwner

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Corporate Training Video Series",
    "poster_url": "<https://s3>.../thumb.jpg",
    "synopsis": "Full synopsis text...",
    "content_link": "<https://vimeo.com/12345>",
    "target_price": 5000.00,
    "currency": "USD",
    "genre_tags": ["Education", "Business"],
    "status": "public",
    "view_count": 246,
    "created_at": "2024-11-15T10:00:00Z",
    "updated_at": "2024-11-15T10:00:00Z"
  }
}

```

---

### **PATCH /api/v1/studio/contents/{id}/**

콘텐츠 수정 (UPL-001~007)

**Permission:** IsAuthenticated, IsProducer, IsOwner

**Request (multipart/form-data, 부분 업데이트):**

```
title: "Updated Title"
target_price: 4500.00
// 변경할 필드만 전송

```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Updated Title",
    "target_price": 4500.00,
    "updated_at": "2024-11-27T11:00:00Z"
    // ... 전체 콘텐츠 정보
  },
  "message": "Content updated successfully"
}

```

---

### **DELETE /api/v1/studio/contents/{id}/**

콘텐츠 삭제 (STD-004)

**Permission:** IsAuthenticated, IsProducer, IsOwner

**Response (200 OK - Soft Delete):**

```json
{
  "success": true,
  "message": "Content deleted successfully"
}

```

**Business Logic:**

- Soft delete: `status='deleted'`로 변경
- 오퍼가 있는 경우 삭제 불가:

**Error (422 Unprocessable Entity):**

```json
{
  "success": false,
  "error": {
    "code": "CANNOT_DELETE_WITH_OFFERS",
    "message": "Cannot delete content with existing offers",
    "details": {
      "offer_count": 3,
      "pending_offers": 1
    }
  }
}

```

---

### **4.5 Offer APIs**

### **POST /api/v1/offers/**

오퍼 제출 (OFR-001~006)

**Permission:** IsAuthenticated, IsBuyer

**Request:**

```json
{
  "content_id": 1,
  "offer_price": 4500.00,
  "currency": "USD",
  "message": "We are interested in acquiring this content for our platform.",
  "validity_days": 14  // 7 | 14 | 30
}

```

**Validation:**

- `content_id`: 존재하는 public 콘텐츠
- `offer_price`: >0
- `currency`: USD/KRW/EUR
- `message`: 최대 500자, 선택
- `validity_days`: 7, 14, 30만 허용

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": 15,
    "content": {
      "id": 1,
      "title": "Corporate Training Video Series",
      "target_price": 5000.00
    },
    "offer_price": 4500.00,
    "currency": "USD",
    "message": "We are interested in...",
    "validity_days": 14,
    "expires_at": "2024-12-11T10:30:00Z",
    "status": "pending",
    "created_at": "2024-11-27T10:30:00Z"
  },
  "message": "Offer submitted successfully"
}

```

**Business Logic:**

- `buyer_id`: 현재 사용자 자동 할당
- `producer_id`: content.producer_id 자동 할당
- `expires_at`: created_at + validity_days 자동 계산
- 이메일 알림 발송 (NTF-001)

**Errors:**

- 404: 콘텐츠 없음
- 409 Conflict: 이미 pending 오퍼 존재 (OFR-006)

```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_OFFER",
    "message": "You already have a pending offer for this content",
    "details": {
      "existing_offer_id": 12
    }
  }
}

```

---

### **GET /api/v1/buyer/offers/**

내가 제출한 오퍼 목록 (OFR-010~011)

**Permission:** IsAuthenticated, IsBuyer

**Query Parameters:**

- `status`: 'pending' | 'accepted' | 'rejected' | 'expired'
- `page`, `page_size`

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": 15,
      "content": {
        "id": 1,
        "title": "Corporate Training Video Series",
        "poster_url": "<https://s3>.../thumb.jpg",
        "producer_name": "MediaCraft Studios"
      },
      "offer_price": 4500.00,
      "currency": "USD",
      "status": "pending",
      "created_at": "2024-11-27T10:30:00Z",
      "expires_at": "2024-12-11T10:30:00Z",
      "url": "/my/offers/15"
    }
  ],
  "pagination": { /* ... */ }
}

```

---

### **GET /api/v1/buyer/offers/{id}/**

내 오퍼 상세 (OFR-020~021)

**Permission:** IsAuthenticated, IsBuyer, IsOwner

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": 15,
    "content": {
      "id": 1,
      "title": "Corporate Training Video Series",
      "poster_url": "<https://s3>.../thumb.jpg",
      "target_price": 5000.00,
      "producer": {
        "company_name": "MediaCraft Studios",
        "country": "United States"
      }
    },
    "offer_price": 4500.00,
    "currency": "USD",
    "message": "We are interested in...",
    "validity_days": 14,
    "expires_at": "2024-12-11T10:30:00Z",
    "status": "pending",
    "created_at": "2024-11-27T10:30:00Z",
    "responded_at": null,
    "loi": null  // accepted 시 LOI 정보
  }
}

```

**When status='accepted':**

```json
{
  // ... 위와 동일
  "status": "accepted",
  "responded_at": "2024-11-28T09:00:00Z",
  "loi": {
    "id": 5,
    "document_number": "LOI-2024-00005",
    "url": "/loi/5"
  }
}

```

---

### **GET /api/v1/studio/offers/**

받은 오퍼 목록 (OFR-030)

**Permission:** IsAuthenticated, IsProducer

**Query Parameters:**

- `status`: 'pending' | 'accepted' | 'rejected' | 'expired'
- `content_id`: 특정 콘텐츠 필터
- `page`, `page_size`

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": 15,
      "content": {
        "id": 1,
        "title": "Corporate Training Video Series",
        "poster_url": "<https://s3>.../thumb.jpg",
        "target_price": 5000.00
      },
      "buyer": {
        "id": 2,
        "company_name": "StreamMax International",
        "country": "Canada"
      },
      "offer_price": 4500.00,
      "currency": "USD",
      "status": "pending",
      "created_at": "2024-11-27T10:30:00Z",
      "expires_at": "2024-12-11T10:30:00Z",
      "url": "/studio/offers/15"
    }
  ],
  "pagination": { /* ... */ },
  "summary": {
    "total": 25,
    "pending": 5,
    "accepted": 15,
    "rejected": 3,
    "expired": 2
  }
}

```

---

### **GET /api/v1/studio/offers/{id}/**

받은 오퍼 상세 (OFR-040~041)

**Permission:** IsAuthenticated, IsProducer, IsOwner (producer)

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": 15,
    "content": {
      "id": 1,
      "title": "Corporate Training Video Series",
      "poster_url": "<https://s3>.../thumb.jpg",
      "target_price": 5000.00,
      "currency": "USD"
    },
    "buyer": {
      "id": 2,
      "company_name": "StreamMax International",
      "country": "Canada",
      "email": "buyer@streammax.com"
    },
    "offer_price": 4500.00,
    "currency": "USD",
    "message": "We are interested in acquiring this content...",
    "validity_days": 14,
    "expires_at": "2024-12-11T10:30:00Z",
    "status": "pending",
    "created_at": "2024-11-27T10:30:00Z",
    "price_comparison": {
      "target_price": 5000.00,
      "offer_price": 4500.00,
      "difference": -500.00,
      "percentage": -10.0
    },
    "actions": {
      "accept": "/studio/offers/15/accept",
      "reject": "/studio/offers/15/reject"
    }
  }
}

```

---

### **POST /api/v1/studio/offers/{id}/accept/**

오퍼 수락 (OFR-042)

**Permission:** IsAuthenticated, IsProducer, IsOwner

**Request:**

```json
{
  "confirm": true
}

```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "offer": {
      "id": 15,
      "status": "accepted",
      "responded_at": "2024-11-28T09:00:00Z"
    },
    "loi": {
      "id": 5,
      "document_number": "LOI-2024-00005",
      "generated_at": "2024-11-28T09:00:00Z",
      "url": "/loi/5"
    }
  },
  "message": "Offer accepted. LOI has been generated."
}

```

**Business Logic:**

- `status`: 'accepted'로 변경
- `responded_at`: 현재 시각
- LOI 자동 생성 (Django signal)
- 이메일 알림 발송 (NTF-002, NTF-004)

**Errors:**

- 422: 이미 응답한 오퍼

```json
{
  "success": false,
  "error": {
    "code": "ALREADY_RESPONDED",
    "message": "This offer has already been responded to",
    "details": {
      "current_status": "rejected"
    }
  }
}

```

---

### **POST /api/v1/studio/offers/{id}/reject/**

오퍼 거절 (OFR-043)

**Permission:** IsAuthenticated, IsProducer, IsOwner

**Request:**

```json
{
  "confirm": true,
  "reason": "Price is too low for this premium content"  // 선택
}

```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "offer": {
      "id": 15,
      "status": "rejected",
      "responded_at": "2024-11-28T09:00:00Z"
    }
  },
  "message": "Offer has been rejected"
}

```

**Business Logic:**

- `status`: 'rejected'로 변경
- 이메일 알림 발송 (NTF-003)

---

### **4.6 LOI APIs**

### **GET /api/v1/loi/**

LOI 문서함 (LOI-001~002)

**Permission:** IsAuthenticated (Producer | Buyer)

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": 5,
      "document_number": "LOI-2024-00005",
      "content_title": "Corporate Training Video Series",
      "counterparty": {
        "company_name": "StreamMax International",
        "country": "Canada"
      },
      "agreed_price": 4500.00,
      "currency": "USD",
      "generated_at": "2024-11-28T09:00:00Z",
      "pdf_url": "<https://s3>.../loi-2024-00005.pdf",
      "url": "/loi/5"
    }
  ],
  "pagination": { /* ... */ }
}

```

**Note:**

- Producer: 자신이 seller인 LOI만 조회
- Buyer: 자신이 buyer인 LOI만 조회

---

### **GET /api/v1/loi/{id}/**

LOI 상세 (LOI-010~012)

**Permission:** IsAuthenticated, IsRelatedParty (buyer 또는 producer)

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": 5,
    "document_number": "LOI-2024-00005",
    "offer": {
      "id": 15,
      "created_at": "2024-11-27T10:30:00Z"
    },
    "content": {
      "id": 1,
      "title": "Corporate Training Video Series",
      "genre_tags": ["Education", "Business"]
    },
    "producer": {
      "company_name": "MediaCraft Studios",
      "country": "United States"
    },
    "buyer": {
      "company_name": "StreamMax International",
      "country": "Canada"
    },
    "agreed_price": 4500.00,
    "currency": "USD",
    "generated_at": "2024-11-28T09:00:00Z",
    "pdf_url": "<https://s3>.../loi-2024-00005.pdf",
    "document_text": "LETTER OF INTENT\\n\\nDocument No: LOI-2024-00005\\n..."
  }
}

```

---

### **GET /api/v1/loi/{id}/download/**

LOI PDF 다운로드 (LOI-011)

**Permission:** IsAuthenticated, IsRelatedParty

**Response:**

- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="LOI-2024-00005.pdf"`
- Binary PDF data

**Errors:**

- 404: LOI 없음
- 403: 권한 없음 (당사자 아님)
- 503: PDF 생성 중 (백그라운드 작업 진행 중)

```json
{
  "success": false,
  "error": {
    "code": "PDF_GENERATING",
    "message": "PDF is being generated. Please try again in a few moments."
  }
}

```

---

### **4.7 Settings APIs**

### **GET /api/v1/settings/profile/**

프로필 조회 (SET-001)

**Permission:** IsAuthenticated

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "producer@example.com",
    "name": "John Doe",
    "user_type": "producer",
    "company_name": "MediaCraft Studios",
    "logo_url": "<https://s3>.../logo.png",
    "country": "United States",
    "genre_tags": ["Drama", "Reality"],
    "booth_slug": "mediacraft-studios"
  }
}

```

---

### **PATCH /api/v1/settings/profile/**

프로필 수정 (SET-001)

**Permission:** IsAuthenticated

**Request:**

```json
{
  "name": "John Smith",
  "company_name": "MediaCraft Studios Inc."
}

```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    // ... 전체 프로필
  },
  "message": "Profile updated successfully"
}

```

---

### **POST /api/v1/settings/change-password/**

비밀번호 변경 (SET-002)

**Permission:** IsAuthenticated

**Request:**

```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass456",
  "new_password_confirm": "NewPass456"
}

```

**Validation:**

- `current_password`: 현재 비밀번호 일치 확인
- `new_password`: 최소 8자, 영문+숫자
- `new_password_confirm`: new_password와 일치

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Password changed successfully"
}

```

**Errors:**

- 400: 현재 비밀번호 불일치

---

### **POST /api/v1/auth/logout/**

로그아웃 (SET-003)

**Permission:** IsAuthenticated

**Request:**

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbG..."
}

```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Logged out successfully"
}

```

**Business Logic:**

- Refresh token을 blacklist에 추가

---

### **4.8 Admin APIs**

### **GET /api/v1/admin/dashboard/**

관리자 대시보드 (ADM-001~005)

**Permission:** IsAuthenticated, IsAdmin

**Query Parameters:**

- `period`: '7d' | '30d' (기본: 7d)

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "summary": {
      "total_users": 250,
      "total_producers": 85,
      "total_buyers": 165,
      "total_contents": 420,
      "total_offers": 1250,
      "pending_offers": 45,
      "total_lois": 380
    },
    "period_stats": {
      "period": "7d",
      "new_users": 12,
      "new_contents": 25,
      "new_offers": 48,
      "new_lois": 15
    },
    "recent_users": [
      {
        "id": 250,
        "email": "newuser@example.com",
        "user_type": "buyer",
        "company_name": "New Company",
        "created_at": "2024-11-27T10:00:00Z"
      }
      // ... 최근 10개
    ],
    "recent_contents": [
      // ... 최근 10개
    ],
    "recent_offers": [
      // ... 최근 10개
    ]
  }
}

```

---

## **5. Error Codes Reference**

### **5.1 Authentication Errors**

| Code | HTTP | 설명 |
| --- | --- | --- |
| `INVALID_CREDENTIALS` | 401 | 이메일/비밀번호 오류 |
| `TOKEN_EXPIRED` | 401 | Access token 만료 |
| `TOKEN_INVALID` | 401 | Token 형식 오류 |
| `ACCOUNT_INACTIVE` | 403 | 계정 비활성화 |
| `EMAIL_DUPLICATE` | 400 | 이메일 중복 |

### **5.2 Business Logic Errors**

| Code | HTTP | 설명 |
| --- | --- | --- |
| `ONBOARDING_REQUIRED` | 403 | 온보딩 미완료 |
| `DUPLICATE_OFFER` | 409 | 중복 오퍼 존재 |
| `CANNOT_DELETE_WITH_OFFERS` | 422 | 오퍼 있어서 삭제 불가 |
| `ALREADY_RESPONDED` | 422 | 이미 응답한 오퍼 |
| `OFFER_EXPIRED` | 422 | 만료된 오퍼 |
| `PDF_GENERATING` | 503 | PDF 생성 중 |

### **5.3 Validation Errors**

| Code | HTTP | 설명 |
| --- | --- | --- |
| `VALIDATION_ERROR` | 400 | 입력 유효성 검증 실패 |
| `INVALID_FILE_TYPE` | 400 | 파일 형식 오류 |
| `FILE_TOO_LARGE` | 400 | 파일 크기 초과 |
| `INVALID_PRICE` | 400 | 가격 형식 오류 |

---

## **6. Rate Limiting**

### **6.1 Rate Limit Policy**

| Endpoint Group | Limit | Period |
| --- | --- | --- |
| Auth (login, register) | 5 requests | 1 minute |
| Content browsing | 100 requests | 1 minute |
| Content management | 30 requests | 1 minute |
| Offer submission | 10 requests | 1 minute |
| General APIs | 60 requests | 1 minute |

### **6.2 Rate Limit Headers**

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1732701600

```

### **6.3 Rate Limit Error (429)**

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "retry_after": 30  // seconds
    }
  }
}

```

---

## **7. File Upload Specifications**

### **7.1 Supported File Types**

| 용도 | 형식 | 최대 크기 | 권장 사양 |
| --- | --- | --- | --- |
| 프로필 로고 | JPG, PNG | 2MB | 1:1, 최소 200x200px |
| 콘텐츠 썸네일 | JPG, PNG | 5MB | 16:9, 최소 1280x720px |

### **7.2 Upload Endpoint**

**POST /api/v1/upload/**

**Request (multipart/form-data):**

```
file: [File]
type: "logo" | "thumbnail"

```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "url": "<https://s3.amazonaws.com/shortdeal/uploads/abc123.jpg>",
    "filename": "logo.jpg",
    "size": 124567,
    "mime_type": "image/jpeg"
  }
}

```

**Errors:**

- 400: 파일 형식/크기 오류
- 413: Payload Too Large

---

## **8. API Versioning & Deprecation**

### **8.1 Version Timeline**

```python
VERSION_TIMELINE = {
    "v1": {
        "released": "2024-12-15",
        "stable": True,
        "deprecated": None,
        "sunset": None,
    },
    "v2": {
        "planned": "2025-Q2",
        "changes": ["GraphQL support", "Webhook events"],
    }
}

```

### **8.2 Deprecation Notice**

Deprecated 엔드포인트는 응답 헤더에 표시:

```
Deprecation: true
Sunset: Wed, 31 Dec 2025 23:59:59 GMT
Link: <https://api.shortdeal.com/v2/endpoint>; rel="successor-version"

```

---

## **9. Testing & Documentation**

### **9.1 Interactive API Docs**

```
Swagger UI:  <https://api.shortdeal.com/docs/>
ReDoc:       <https://api.shortdeal.com/redoc/>
OpenAPI:     <https://api.shortdeal.com/openapi.json>

```

### **9.2 Postman Collection**

Export 후 공유:

```
<https://api.shortdeal.com/postman/collection.json>

```

### **9.3 Example Requests**

각 엔드포인트에 curl 예시:

```bash
# 회원가입
curl -X POST <https://api.shortdeal.com/v1/auth/register/> \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "producer@example.com",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123",
    "name": "John Doe",
    "user_type": "producer"
  }'

# 콘텐츠 조회 (with token)
curl -X GET <https://api.shortdeal.com/v1/contents/?q=drama> \\
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbG..."

```

---

## **10. Security Best Practices**

### **10.1 HTTPS Only**

- 모든 API는 HTTPS 필수
- HTTP 요청은 301 → HTTPS

### **10.2 CORS Configuration**

```python
CORS_ALLOWED_ORIGINS = [
    "<https://shortdeal.com>",
    "<https://www.shortdeal.com>",
]

CORS_ALLOW_CREDENTIALS = True

```

### **10.3 Content Security**

- File upload: 바이러스 스캔 (ClamAV)
- Input sanitization: XSS 방지
- SQL Injection 방지: Django ORM 사용

---

## **11. Performance Optimization**

### **11.1 Caching Strategy**

| 리소스 | 캐시 | TTL |
| --- | --- | --- |
| 콘텐츠 목록 | Redis | 5분 |
| 콘텐츠 상세 | Redis | 10분 |
| 사용자 프로필 | Redis | 30분 |

### **11.2 Database Query Optimization**

```python
# N+1 문제 방지
contents = Content.objects.select_related(
    'booth', 'producer'
).prefetch_related(
    'offers'
).all()

```

### **11.3 Pagination**

- 기본: 20개/페이지
- 최대: 100개/페이지
- Cursor-based pagination (Phase 2)

---

## **12. Monitoring & Logging**

### **12.1 API Metrics**

- Response time (p50, p95, p99)
- Error rate by endpoint
- Request volume by endpoint

### **12.2 Logging Format**

```json
{
  "timestamp": "2024-11-27T10:30:00Z",
  "level": "INFO",
  "method": "POST",
  "path": "/api/v1/offers/",
  "user_id": 2,
  "status_code": 201,
  "response_time_ms": 145,
  "ip": "203.0.113.1"
}

```

---

## **13. Future Enhancements (Phase 2)**

### **13.1 Planned Features**

```python
PHASE_2_FEATURES = {
    "Webhooks": "오퍼 수락/거절 시 callback",
    "GraphQL": "복잡한 쿼리 최적화",
    "Real-time": "WebSocket (알림)",
    "Bulk Operations": "일괄 콘텐츠 업로드",
    "Analytics": "콘텐츠 성과 분석 API",
    "Multi-currency": "실시간 환율 변환",
}

```

---

## **Appendix A: Full Endpoint List**

### **Authentication**

- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/refresh/`
- `GET /api/v1/auth/me/`
- `POST /api/v1/auth/logout/`

### **Onboarding**

- `POST /api/v1/onboarding/producer/`
- `POST /api/v1/onboarding/buyer/`

### **Content Browsing**

- `GET /api/v1/contents/`
- `GET /api/v1/contents/{id}/`
- `GET /api/v1/booths/{slug}/`

### **Content Management (Producer)**

- `GET /api/v1/studio/contents/`
- `POST /api/v1/studio/contents/`
- `GET /api/v1/studio/contents/{id}/`
- `PATCH /api/v1/studio/contents/{id}/`
- `DELETE /api/v1/studio/contents/{id}/`

### **Offers (Buyer)**

- `POST /api/v1/offers/`
- `GET /api/v1/buyer/offers/`
- `GET /api/v1/buyer/offers/{id}/`

### **Offers (Producer)**

- `GET /api/v1/studio/offers/`
- `GET /api/v1/studio/offers/{id}/`
- `POST /api/v1/studio/offers/{id}/accept/`
- `POST /api/v1/studio/offers/{id}/reject/`

### **LOI**

- `GET /api/v1/loi/`
- `GET /api/v1/loi/{id}/`
- `GET /api/v1/loi/{id}/download/`

### **Settings**

- `GET /api/v1/settings/profile/`
- `PATCH /api/v1/settings/profile/`
- `POST /api/v1/settings/change-password/`

### **Admin**

- `GET /api/v1/admin/dashboard/`

### **Utility**

- `POST /api/v1/upload/`

---

## **Appendix B: Django URL Configuration**

```python
# api/urls.py
from django.urls import path, include

urlpatterns = [
    path('v1/auth/', include('accounts.urls')),
    path('v1/onboarding/', include('onboarding.urls')),
    path('v1/contents/', include('contents.urls')),
    path('v1/booths/', include('booths.urls')),
    path('v1/studio/', include('studio.urls')),
    path('v1/offers/', include('offers.urls')),
    path('v1/buyer/', include('buyer.urls')),
    path('v1/loi/', include('loi.urls')),
    path('v1/settings/', include('settings.urls')),
    path('v1/admin/', include('admin_api.urls')),
    path('v1/upload/', include('upload.urls')),
]

```

---

## **변경 이력**

| 버전 | 날짜 | 변경 내용 |
| --- | --- | --- |
| 1.0 | 2024-11-27 | 초안 작성 (REST API 전체) |

---