# SendGrid 이메일 설정 가이드

Railway에서 Gmail SMTP가 작동하지 않을 때 SendGrid를 사용하세요.

## SendGrid 설정 (무료)

### 1. SendGrid 계정 생성
1. https://sendgrid.com/ 접속
2. 회원가입 (무료 플랜: 하루 100개 이메일)
3. 이메일 인증 완료

### 2. API Key 생성
1. Settings → API Keys
2. "Create API Key" 클릭
3. 이름: "ShortDeal Railway"
4. Permissions: "Full Access" 또는 "Mail Send"만 선택
5. API Key 복사 (SG.로 시작하는 긴 문자열)

### 3. Sender Identity 설정
1. Settings → Sender Authentication
2. "Single Sender Verification" 선택
3. 발신자 정보 입력:
   - From Email: noreply@yourdomain.com 또는 your-email@gmail.com
   - From Name: ShortDeal
4. 이메일 인증 완료

### 4. Railway 환경변수 설정

```bash
# SendGrid SMTP 설정
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your-actual-api-key-here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com  # 위에서 인증한 이메일

# 또는 환경변수 제거하고 기본값 사용:
# EMAIL_BACKEND 제거 (기본: SMTP)
```

### 5. 배포 및 테스트

Railway에서 자동 배포되면 로그 확인:
```
Email configuration: BACKEND=django.core.mail.backends.smtp.EmailBackend,
HOST=smtp.sendgrid.net, PORT=587, TLS=True, USER=[SET], PASSWORD=[SET]
```

## 대안: Mailgun

무료 플랜: 월 1000개 이메일

### Mailgun 환경변수:
```bash
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@your-domain.mailgun.org
EMAIL_HOST_PASSWORD=your-mailgun-password
DEFAULT_FROM_EMAIL=noreply@your-domain.mailgun.org
```

## 대안: AWS SES

저렴하고 안정적 (월 62,000개 무료)

### AWS SES 환경변수:
```bash
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-ses-smtp-username
EMAIL_HOST_PASSWORD=your-ses-smtp-password
DEFAULT_FROM_EMAIL=verified@yourdomain.com
```

## 임시: Console Backend (테스트용)

이메일을 실제로 보내지 않고 로그에만 출력:

```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

이 경우 Railway 로그에서 이메일 내용을 확인할 수 있습니다.

## Gmail이 안 되는 이유

Railway는 보안상의 이유로 일부 SMTP 포트를 제한합니다:
- Port 25: 차단됨
- Port 587: 제한적
- Gmail: 추가 보안으로 Railway에서 연결 어려움

**권장: SendGrid 또는 Mailgun 사용**
