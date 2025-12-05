# Railway Volume 설정 가이드

업로드된 미디어 파일(이미지, PDF 등)을 재배포 후에도 유지하려면 Railway Volume을 설정해야 합니다.

## Volume이 없으면 어떻게 되나요?

- 업로드된 파일은 컨테이너의 `/app/media` 폴더에 저장됩니다
- **재배포 시 모든 업로드 파일이 삭제됩니다**
- 개발/테스트 단계에서는 괜찮지만, 프로덕션에서는 문제가 됩니다

## Railway Volume 설정 방법

### 1. Railway Dashboard에서 Volume 생성

1. Railway 프로젝트로 이동
2. 우측 상단 **+ Create** 버튼 클릭
3. **Volume** 선택
4. Volume 이름 입력 (예: `shortdeal-media`)
5. **Create** 클릭

### 2. Volume을 서비스에 마운트

1. 생성된 Volume 클릭
2. **Mount** 또는 **Connect** 버튼 클릭
3. 서비스 선택 (shortdeal-be)
4. **Mount Path** 입력: `/app/media`
5. **Mount** 또는 **Connect** 클릭

### 3. 재배포

Volume 설정 후 자동으로 재배포됩니다. 이후 업로드된 모든 파일은 Volume에 저장되어 재배포 후에도 유지됩니다.

### 4. 확인

1. Railway 로그에서 확인:
   ```
   railway logs
   ```

2. 미디어 파일 업로드 테스트
3. 재배포 후 파일이 여전히 존재하는지 확인

## 현재 설정

- **Media URL**: `/media/`
- **Media Root**: `/app/media` (프로덕션)
- **Local Media Root**: `./media` (로컬 개발)

## 비용

Railway Volume은 GB당 월 $0.25입니다. 예상 사용량:
- 이미지 파일: 평균 500KB
- PDF 파일: 평균 2MB
- 1000개 파일 = 약 1-2GB = 월 $0.25-0.50

## 대안: 클라우드 스토리지

나중에 트래픽이 증가하면 다음을 고려하세요:

1. **AWS S3**: 가장 널리 사용되는 옵션
2. **Cloudflare R2**: S3 호환, egress 비용 없음
3. **Backblaze B2**: 저렴한 대안

django-storages를 사용하면 쉽게 마이그레이션할 수 있습니다.

## 문제 해결

### Volume이 마운트되지 않음

Railway 로그에서 다음 확인:
```
ls -la /app/media
```

### 권한 문제

Dockerfile에서 media 폴더 생성:
```dockerfile
RUN mkdir -p /app/media && chmod 755 /app/media
```

### 기존 파일 마이그레이션

Volume 설정 전 업로드된 파일은 복구할 수 없습니다. Volume 설정 후 새로 업로드해야 합니다.
