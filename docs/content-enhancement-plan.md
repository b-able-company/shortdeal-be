# 콘텐츠 확장 적용 계획

## 개요
- 추가 요청: 세로형 포스터 업로드, 영상 등급(전체/12/15/19), 희망 릴리즈 시기, 내부 워터마크 스크리너 재생.
- 대상 범위: 콘텐츠 모델/시리얼라이저/API 스펙, 업로드·수정·상세 템플릿, 검증/상수, 어드민, 테스트·문서.

## 작업 단계
1) 모델/상수/마이그레이션
- `apps/contents/models.py`: `poster`, `rating`, `release_target`, `screener_url` 필드 추가.
- `apps/core/constants.py`: 등급 상수(`all/12/15/19`), 포스터 업로드 제한 추가.
- `apps/core/validators.py`: 포스터 파일 검증 추가.
- 마이그레이션 생성.

2) 시리얼라이저/API
- `apps/contents/serializers.py`: 새 필드 포함(공개/상세/CRUD/생성·수정).
- `docs/api-spec.md`, 필요 시 `docs/db-schema.md`에 필드/제약 업데이트.

3) 뷰/서비스 로직
- `apps/contents/views.py`: 업로드/수정 시 새 필드 검증·저장(포스터 optional, 등급 선택, 릴리즈 date optional, 스크리너 URL optional).
- 리스트/삭제 로직 영향 검토.

4) 템플릿/UI
- `templates/contents/studio_create.html`, `studio_edit.html`: 포스터 업로드 필드, 등급 드롭다운, 희망 릴리즈 date 입력, 스크리너 URL 입력 추가.
- `templates/contents/detail.html` 등 상세/리스트: 포스터(없으면 썸네일) 우선 표시, 등급·릴리즈 시기 표시, 스크리너 인앱 플레이(워터마크 오버레이) 섹션 추가.
- 콘텐츠 링크 버튼은 외부, 스크리너는 내부 재생으로 구분.

5) 어드민/검증
- `apps/contents/admin.py`: 새 필드 노출/필터 추가.
- 파일/입력 검증 메시지 정비.

6) 테스트
- 모델/마이그레이션 기본값 확인.
- 시리얼라이저 필드 포함·검증 유닛 테스트.
- 스튜디오 업로드/수정 통합 테스트: 새 필드 처리·저장 검증.

7) 문서/가이드
- 필요 시 튜토리얼/헬프 텍스트(templates/tutorial.html 등) 업데이트로 새 필드 안내.

## 주의사항
- 이미지 검증: JPEG/PNG, 포스터 5MB 이하.
- P0 스코프 내 기능만 추가, 기존 워크플로우/퍼미션 유지.
- Soft delete/오퍼 제약 영향 없음 확인.
