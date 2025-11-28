# Django Language Configuration Guide

## 📝 변경 사항

### 1. 설정 변경 (settings/base.py)
```python
# 이전 (한글)
LANGUAGE_CODE = 'ko-kr'

# 변경 후 (영어)
LANGUAGE_CODE = 'en-us'
```

**효과:**
- Django Admin 인터페이스가 자동으로 영어로 변환
- 에러 메시지가 영어로 표시
- 날짜/시간 형식이 영어 포맷으로 변경

### 2. 템플릿 파일 변경
모든 하드코딩된 한글을 영어로 변경:
- `templates/home.html` ✅
- `templates/includes/navbar.html` ✅
- `templates/base.html` (footer 추가) ✅

---

## 🔍 다국어 지원이 필요하면?

만약 나중에 **한글/영어를 동시에** 지원해야 한다면, 이때 국제화(i18n) 설정을 추가하면 됩니다.

### 그때 추가할 설정:

#### Step 1: settings/base.py에 추가
```python
from django.utils.translation import gettext_lazy as _

MIDDLEWARE = [
    ...
    'django.middleware.locale.LocaleMiddleware',  # 추가
    ...
]

LANGUAGES = [
    ('en-us', _('English')),
    ('ko-kr', _('Korean')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
```

#### Step 2: 템플릿에서 `{% trans %}` 태그 사용
```html
<!-- 이렇게 변경 -->
<h1>{% trans "Welcome to ShortDeal" %}</h1>

<!-- 변수가 있으면 -->
<p>{% blocktrans %}Welcome, {{ username }}!{% endblocktrans %}</p>
```

#### Step 3: 번역 파일 생성
```bash
python manage.py makemessages -l ko
python manage.py makemessages -l en
# 번역 파일을 편집한 후
python manage.py compilemessages
```

---

## ✅ 현재 상태

**언어**: 영어 (en-us)  
**시간대**: 서울 (Asia/Seoul)  
**국제화**: 비활성화 (필요시 추후 활성화 가능)

---

## 🚀 다음 단계

지금은 영어로만 서비스하고, 나중에 다국어가 필요하면 알려주세요. 그때 i18n 설정을 추가하겠습니다.
