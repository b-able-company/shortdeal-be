# ShortDeal Frontend 설정 완료

## ✅ 완료된 작업

### 1. Bootstrap + Bootswatch 테마 통합
- **파일**: `static/css/bootstrap.min.css`
- **상태**: 준비됨 (Bootswatch United 테마)
- **설명**: 현대적이고 세련된 디자인을 제공합니다

### 2. 커스텀 CSS 추가
- **파일**: `static/css/custom.css`
- **포함 내용**:
  - 색상 팔레트 정의 (Primary, Secondary, Accent 등)
  - 타이포그래피 설정 (글꼴, 크기, 간격)
  - 컴포넌트 스타일 (버튼, 카드, 폼, 테이블 등)
  - 반응형 디자인 (모바일/태블릿 지원)
  - 커스텀 컴포넌트 (부스 카드, 배지 등)
  - 호버 효과 및 전환 애니메이션

### 3. Django 템플릿 구조
```
templates/
├── base.html           ✅ Bootstrap + CSS 로드 설정 완료
├── home.html          ✅ 랜딩 페이지 완성 (기능별 소개, CTA 포함)
└── includes/
    ├── navbar.html    ✅ 네비게이션 바 개선 (로그인 상태, 배지 표시)
    └── messages.html  ✅ 메시지 표시 (이미 스타일 적용됨)
```

### 4. Django Bootstrap5 통합
- **패키지**: `django-bootstrap5`
- **용도**: Bootstrap JavaScript 및 기본 스타일 제공
- **로드 방식**: `{% bootstrap_css %}`, `{% bootstrap_javascript %}`

## 🎨 디자인 특징

### 색상 팔레트
- **Primary**: `#007bff` (파란색) - 기본 색상
- **Accent**: `#ff6b6b` (빨간색) - 강조 색상
- **Success**: `#51cf66` (초록색) - 성공 상태
- **Dark**: `#343a40` - 다크 모드

### 컴포넌트
- **카드**: 그림자, 호버 효과, 부드러운 코너
- **버튼**: 다양한 크기, 색상, 상태
- **폼**: 스타일된 입력 필드, 포커스 효과
- **네비게이션**: 반응형 모바일 메뉴
- **배지**: 역할 표시용 배지

## 📁 파일 구조

```
shortdeal-be/
├── static/
│   ├── css/
│   │   ├── bootstrap.min.css  (Bootswatch 테마)
│   │   └── custom.css         (커스텀 스타일)
│   └── js/                    (필요시 JavaScript 파일)
├── templates/
│   ├── base.html
│   ├── home.html
│   └── includes/
│       ├── navbar.html
│       └── messages.html
└── shortdeal/
    └── settings/
        └── base.py            (STATIC_URL, STATICFILES_DIRS 설정 완료)
```

## 🚀 사용 방법

### 개발 서버 실행
```bash
python manage.py runserver
```

### 정적 파일 수집 (프로덕션)
```bash
python manage.py collectstatic
```

### Docker 실행
```bash
docker-compose up
```

## 📝 주의사항

1. **django-bootstrap5** 패키지가 반드시 설치되어야 합니다
   ```bash
   pip install django-bootstrap5
   ```

2. **Static 파일 캐싱**: 브라우저 캐싱으로 인해 CSS 변경이 반영되지 않을 수 있습니다
   - 개발 중: Ctrl+Shift+Delete로 캐시 삭제
   - 변경: `python manage.py findstatic` 후 새로고침

3. **CSRF 토큰**: 폼에서 반드시 `{% csrf_token %}` 포함 필요

## 🎯 다음 단계

1. **템플릿 추가** (P0 기능별)
   - `accounts/producer_onboarding.html` - 제작사 부스 생성
   - `accounts/buyer_dashboard.html` - 바이어 대시보드
   - `contents/content_list.html` - 콘텐츠 검색/필터
   - `offers/offer_create.html` - 제안 생성
   - `loi/loi_view.html` - LOI 조회

2. **커스텀 CSS 확장**
   - 각 페이지별 추가 스타일
   - 애니메이션 및 인터랙션
   - 다크 모드 (필요시)

3. **테스트**
   - 반응형 디자인 확인 (모바일, 태블릿)
   - 크로스 브라우저 호환성 확인

## 📞 설정 파일

### settings/base.py (이미 설정됨)
```python
INSTALLED_APPS = [
    ...
    'django_bootstrap5',
    ...
]

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        ...
    }
]
```

---

**작성일**: 2025-01-XX  
**상태**: ✅ 준비 완료  
**다음 작업**: P0 기능 템플릿 작성 및 뷰 개발
