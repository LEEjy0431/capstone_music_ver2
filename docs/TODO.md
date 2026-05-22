# TODO — 피아노 연주 자동 평가 시스템

> 마지막 업데이트: 2026-05-22  
> 브랜치: `kts`

---

## 0. 환경 설정 (신규 팀원 온보딩)

| 상태 | 항목 | 담당 | 비고 |
|------|------|------|------|
| ✅ | `code/environment.yml` 작성 (Anaconda) | main 관리자 | Mac Apple Silicon 주석 포함 |
| ✅ | `docs/GUIDE_MAC.md` 작성 | — | Mac 전체 스택 설치 가이드 |
| ✅ | `docs/AGENT_GUIDELINES.md` 작성 | — | 영역별 수정 규칙, 금지 사항 |
| 🔴 | 팀원 Mac에서 `conda env create` 검증 | 팀원 각자 | `conda activate capstone_music` 후 테스트 실행 |
| 🔴 | Apple Silicon TensorFlow 설치 확인 | 팀원 (Mac) | `tensorflow-macos` 수동 교체 필요 |
| 🟡 | `onnxruntime-silicon` 필요 여부 확인 | main 관리자 | Apple Silicon에서 `onnxruntime` 오류 시 교체 |

---

## 우선순위 범례

| 기호 | 의미 |
|------|------|
| 🔴 | 필수 (블로킹) |
| 🟡 | 중요 (다음 스프린트) |
| 🟢 | 개선 (여유 시) |
| ✅ | 완료 |

---

## 1. Flutter 앱 (메인 클라이언트)

### 1-1. 환경 / 빌드

| 상태 | 항목 | 비고 |
|------|------|------|
| 🔴 | `flutter pub get` 실행 및 의존성 충돌 확인 | `pubspec.yaml` 기준 |
| 🔴 | Android APK 빌드 검증 (`flutter build apk`) | 에뮬레이터 또는 실기기 |
| 🟡 | API_BASE 환경 분리 (개발 / 운영) | `--dart-define` 활용 |
| 🟡 | 앱 아이콘 / 스플래시 화면 설정 | `flutter_launcher_icons` 패키지 |

### 1-2. 기능

| 상태 | 항목 | 비고 |
|------|------|------|
| ✅ | `POST /api/analyze` 연동 — 채점 결과 + `session_id` 수신 | Sprint 6 완료 |
| ✅ | `GET /api/feedback/stream` SSE 연동 — `session_id` 방식 | Sprint 6 완료 |
| ✅ | SSE `done` 이벤트 수신 후 provider 피드백 동기화 | Sprint 6 완료 |
| 🔴 | 분석 기록 로컬 저장 | 현재 메모리만 → `shared_preferences` 직렬화 |
| 🟡 | 앱 재시작 시 기록 복원 | JSON 인코딩 후 저장 |
| 🟡 | 파일 선택 오류 처리 (취소, 용량 초과) | try-catch + 사용자 안내 |
| 🟡 | 분석 중 취소 기능 | HTTP 요청 abort |
| 🟢 | 레이더 차트 (리듬/음정/타이밍) | `fl_chart` RadarChart |
| 🟢 | 연습 히트맵 (날짜별 분포) | 16주 × 7일 |
| 🟢 | 결과 공유 (이미지 저장 / 링크) | `screenshot` 패키지 |

### 1-3. UI / 다크모드

| 상태 | 항목 | 비고 |
|------|------|------|
| 🟡 | 다크모드 설정 영속화 | `shared_preferences` |
| 🟡 | 로딩 스켈레톤 UI | 분석 대기 중 |
| 🟢 | 애니메이션 (점수 카운트업) | `AnimatedBuilder` |

---

## 2. Go 백엔드

| 상태 | 항목 | 비고 |
|------|------|------|
| ✅ | `POST /api/analyze` — 채점 결과 + `session_id` 즉시 반환 | Sprint 6 완료 |
| ✅ | `GET /api/feedback/stream` — `session_id` 조회 방식으로 교체 | Sprint 6 완료 |
| ✅ | `backend/services/store.go` — 세션 스토어 (TTL 5분) 구현 | Sprint 6 완료 |
| 🔴 | 환경변수 `.env` 자동 로딩 (`godotenv`) | 현재 수동 export 필요 |
| 🟡 | 파일 크기 제한 명시 (현재 50MB) | 필요 시 조정 |
| 🟡 | 분석 타임아웃 설정 | Python 실행 > 3분 방어 |
| 🟡 | 에러 로깅 구조화 (`log/slog`) | 운영 환경 디버깅 |
| 🟢 | `/api/history` 엔드포인트 (서버 저장 방식 전환 시) | DB 연동 필요 |
| 🟢 | Rate limiting | 동시 분석 요청 제한 |

---

## 3. Python 파이프라인

| 상태 | 항목 | 비고 |
|------|------|------|
| 🔴 | Linux 서버에서 `requirements.txt` 설치 검증 | `piano_transcription_inference` 포함 |
| 🟡 | `module2.py` CPU vs GPU 자동 선택 | `torch.cuda.is_available()` |
| 🟡 | BPM 미감지 시 폴백 로직 강화 | 현재 120 고정 |
| 🟡 | 채점 파라미터 노출 (time_tolerance, chord_tolerance) | API 또는 환경변수 |
| 🟢 | module3 채점 알고리즘 개선 (Dynamic Time Warping) | 음표 정렬 정확도 향상 |
| 🟢 | 지원 파일 형식 확장 (MP3 → WAV 자동 변환) | `pydub` |

---

## 4. 인프라 / 배포

| 상태 | 항목 | 비고 |
|------|------|------|
| 🟡 | Docker Compose 구성 (Go + Python) | 단일 명령 실행 |
| 🟡 | Flutter Web 정적 파일을 Go 서버에서 서빙 | `embed` 패키지 |
| 🟢 | CI/CD 파이프라인 (GitHub Actions) | 빌드 + 테스트 자동화 |
| 🟢 | HTTPS 설정 (Certbot / Nginx 리버스프록시) | Android 운영 배포 필요 |

---

## 5. 테스트

| 상태 | 항목 | 비고 |
|------|------|------|
| 🟡 | Python 파이프라인 단위 테스트 (`pytest`) | module1~3 |
| 🟡 | Go 핸들러 테스트 (`net/http/httptest`) | /api/analyze mock |
| 🟢 | Flutter 위젯 테스트 (`flutter_test`) | ScoreBar, FeedbackCard |
| 🟢 | E2E 테스트 시나리오 문서화 | 샘플 파일 기반 |

---

## 6. 문서

| 상태 | 항목 | 비고 |
|------|------|------|
| 🟡 | 이 파일 (`docs/TODO.md`) 주기적 업데이트 | 작업 완료 시 ✅ 표시 |
| 🟡 | `docs/PROGRESS.md` 진행 누적 기록 | 스프린트 단위 |
| 🟢 | API 명세 OpenAPI (Swagger) 변환 | 자동 생성 도구 활용 |
