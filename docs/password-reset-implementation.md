# Password Reset Implementation Summary

비밀번호 재설정 기능이 성공적으로 구현되었습니다.

## 구현된 기능

### 1. API 엔드포인트 (JWT)

#### 비밀번호 재설정 요청
- **URL**: `POST /api/v1/auth/password-reset/request/`
- **Permission**: AllowAny
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response** (항상 200 OK - 사용자 열거 방지):
  ```json
  {
    "success": true,
    "data": {},
    "message": "If the email exists, a reset link has been sent."
  }
  ```

#### 비밀번호 재설정 확인
- **URL**: `POST /api/v1/auth/password-reset/confirm/`
- **Permission**: AllowAny
- **Request Body**:
  ```json
  {
    "uid": "<uidb64>",
    "token": "<token>",
    "new_password": "newpassword123",
    "new_password_confirm": "newpassword123"
  }
  ```
- **Success Response** (200 OK - 자동 로그인 토큰 포함):
  ```json
  {
    "success": true,
    "data": {
      "user": { /* user object */ },
      "tokens": {
        "refresh": "...",
        "access": "..."
      }
    },
    "message": "Password has been reset successfully."
  }
  ```

### 2. 웹 UI (Django Templates)

#### 비밀번호 재설정 요청 페이지
- **URL**: `/accounts/password-reset/`
- **Template**: `templates/accounts/password_reset_request.html`
- **기능**: 이메일 주소 입력 후 재설정 링크 전송

#### 비밀번호 재설정 확인 페이지
- **URL**: `/accounts/password-reset/confirm/<uidb64>/<token>/`
- **Template**: `templates/accounts/password_reset_confirm.html`
- **기능**: 새 비밀번호 설정 (토큰 검증 포함)

#### 로그인 페이지 업데이트
- "Forgot password?" 링크 추가

### 3. 이메일 알림

비밀번호 재설정 이메일이 자동으로 발송됩니다:
- 재설정 링크 포함
- 24시간 만료 안내
- 사용자 친화적인 메시지

### 4. 보안 기능

✅ **사용자 열거 방지**: 존재하지 않는 이메일에도 동일한 메시지 반환
✅ **토큰 기반 검증**: Django의 PasswordResetTokenGenerator 사용
✅ **비밀번호 강도 검증**: Django의 validate_password 적용
✅ **토큰 만료**: 비밀번호 변경 후 토큰 자동 무효화
✅ **대소문자 무시**: 이메일 조회 시 대소문자 구분 안 함

### 5. 테스트

모든 테스트 통과 (14개):
- ✅ API 엔드포인트 테스트 (9개)
- ✅ 웹 뷰 테스트 (5개)

테스트 실행:
```bash
uv run python manage.py test apps.accounts.tests.PasswordResetAPITestCase
uv run python manage.py test apps.accounts.tests.PasswordResetWebViewTestCase
```

## 파일 변경 사항

### 새로 생성된 파일
- `apps/accounts/tests.py` - 통합 테스트
- `templates/accounts/password_reset_request.html` - 재설정 요청 페이지
- `templates/accounts/password_reset_confirm.html` - 재설정 확인 페이지

### 수정된 파일
- `apps/accounts/serializers.py` - PasswordResetRequestSerializer, PasswordResetConfirmSerializer 추가
- `apps/accounts/api_views.py` - PasswordResetRequestView, PasswordResetConfirmView 추가
- `apps/accounts/api_urls.py` - API URL 라우팅 추가
- `apps/accounts/forms.py` - PasswordResetRequestForm, PasswordResetConfirmForm 추가
- `apps/accounts/views.py` - password_reset_request_view, password_reset_confirm_view 추가
- `apps/accounts/urls.py` - 웹 URL 라우팅 추가
- `apps/notifications/emails.py` - send_password_reset_email 함수 추가
- `templates/accounts/login.html` - "Forgot password?" 링크 추가

## 환경 변수

`.env` 파일에 다음 변수 추가 권장:

```env
# Frontend URL for password reset (API uses this)
FRONTEND_URL=http://localhost:3000

# Email settings (already configured)
DEFAULT_FROM_EMAIL=noreply@shortdeal.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

## 사용 흐름

### API (프론트엔드/모바일)
1. 사용자가 이메일 입력
2. `POST /api/v1/auth/password-reset/request/` 호출
3. 이메일 수신 (프론트엔드 URL 포함)
4. 프론트엔드에서 uid, token 추출
5. `POST /api/v1/auth/password-reset/confirm/` 호출
6. 자동 로그인 (JWT 토큰 반환)

### 웹 UI
1. 로그인 페이지에서 "Forgot password?" 클릭
2. 이메일 주소 입력
3. 이메일 수신 (웹 URL 포함)
4. 링크 클릭하여 새 비밀번호 입력
5. 로그인 페이지로 리다이렉트

## 다음 단계 (선택사항)

1. **Rate Limiting**: DRF throttle 클래스로 요청 제한 추가
2. **프론트엔드 통합**: React/Vue 앱에서 API 엔드포인트 연결
3. **이메일 템플릿**: HTML 이메일 템플릿 디자인 개선
4. **다국어 지원**: 이메일 내용 번역 추가
