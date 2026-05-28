# PROGRESS — 피아노 연주 자동 평가 시스템 개발 기록

> 누적 진행 가이드. 작업이 완료될 때마다 해당 스프린트 항목에 추가한다.  
> 브랜치: `kts` | 저장소: `https://github.com/LEEjy0431/capstone_music_ver2`

---

## 작성 규칙

```
## [Sprint N] YYYY-MM-DD — 스프린트 제목
### 완료 항목
- 파일명 또는 기능 설명 (간략히)
### 주요 결정 사항
- 기술 선택, 트레이드오프 등
### 발생한 문제 & 해결
- 문제 요약 → 원인 → 해결책
### 다음 스프린트 예정
- ...
```

---

## [Sprint 1] 2026-04-XX — Python 분석 파이프라인 구축

### 완료 항목
- `code/module1.py`: MusicXML → 음표 추출 (music21)
- `code/module2.py`: WAV → 음표 추출 (piano_transcription_inference)
- `code/module3.py`: 음표 비교 및 채점 (time_tolerance 0.2s, chord_tolerance 0.05s)
- `code/main.py`: CLI 진입점, `--sheet` / `--audio` 인자

### 주요 결정 사항
- **piano_transcription_inference** 선택: librosa onset 대비 피아노 특화 정확도 우수
- 채점 기준: `score = correct / total × 100`, 타이밍 오차 0.2초

### 발생한 문제 & 해결
- `tensorflow-macos`가 Linux에서 설치 실패
  → `requirements-mac.txt`로 분리

---

## [Sprint 2] 2026-04-XX — GPT 피드백 모듈 추가

### 완료 항목
- `code/module4.py`: OpenAI GPT-4o-mini 기반 피드백 생성
  - `generate_feedback(score, lang)` 함수
  - `response_format: json_object` 사용 (구조 보장)
  - 지원 언어: ko / en / ja / zh
- `code/main.py` 확장: `--json`, `--feedback`, `--lang` 플래그 추가
- `requirements-llm.txt` 신규: `openai>=1.30.0`, `python-dotenv`

### 주요 결정 사항
- **GPT-4o-mini** 선택: 비용 대비 품질 균형, 다국어 성능 양호
- Python에서 직접 GPT 호출하는 방식 (나중에 Go 서버 호출 방식으로 전환)

### 발생한 문제 & 해결
- `module1.py`의 BPM 출력(`print(f"-> BPM 감지: {bpm}")`)이 stdout을 오염
  → 모든 진단 출력을 `print(..., file=sys.stderr)`로 변경
  → `--json` 모드에서 stdout은 순수 JSON만 출력

---

## [Sprint 3] 2026-05-XX — Go 백엔드 서버 구축

### 완료 항목
- `backend/main.go`: HTTP 서버 (포트 8080), `POST /api/analyze`, `GET /health`
- `backend/models/types.go`: `ScoreResult`, `FeedbackResult`, `AnalyzeResponse`, `ErrorResponse`
- `backend/handlers/analyze.go`: multipart 파일 수신 → 임시 파일 저장 → Python 호출 → 응답
- `backend/services/python_runner.go`: Python subprocess 실행, stdout JSON 파싱
- `backend/services/gpt.go`: OpenAI API 호출 (Go SDK), 60초 타임아웃
- `backend/services/i18n.go`: 언어별 system/user 프롬프트 생성

### 주요 결정 사항
- **Go net/http** 선택: 의존성 최소화, 바이너리 단일 배포
- Go에서 GPT 호출 (Python module4 대신): 서버 계층에서 언어/비용 제어 가능
- Python subprocess `--json` 모드: stdout=JSON, stderr=진단로그

### 발생한 문제 & 해결
- `runtime.Caller(0)`으로 `code/main.py` 경로 탐색 → 컴파일 바이너리에서 실패
  → `PROJECT_ROOT` 환경변수 우선, `os.Executable()` 폴백으로 수정
- CORS를 핸들러 내부에 중첩 정의 → Flutter Web에서 preflight 미처리
  → `backend/main.go`에 최상위 `corsHandler` 미들웨어로 이동 (Sprint 5에서 해결)

---

## [Sprint 4] 2026-05-XX — React 프론트엔드 API 연동 + 문서화

### 완료 항목
- `src/App.jsx`: `addRecord()` → `fetch POST /api/analyze` 실제 연동
- `src/AnalysisPage.jsx`: FileDropZone(WAV/XML), 언어 선택, 결과 카드, FeedbackCard
- `.env.example` 업데이트: `PROJECT_ROOT`, `VITE_API_BASE` 추가
- `README.md` (루트): Level 0/1/2 DFD, 기술 스택 표, 단계별 실행 가이드, API 명세, 트러블슈팅
- `backend/README.md`: DFD, 환경변수 표, API 명세
- `code/README.md`: 모듈별 DFD, CLI 옵션 표, 채점 기준
- `src/README.md`: 컴포넌트 트리 DFD, 전역 상태 스키마, 테마 토큰 표
- 스택별 requirements 분리: `requirements.txt` / `requirements-llm.txt` / `requirements-mac.txt` / `requirements-go.txt` / `requirements-node.txt`

### 주요 결정 사항
- React 프론트엔드는 임시 유지 (Flutter 전환 전 MVP 검증용)
- DFD는 Level 0 (컨텍스트) → Level 1 (주요 흐름) → Level 2 (데이터 상세) 3단계로 표준화

### 발생한 문제 & 해결
- git push 403: `kimtaesung98` 계정 권한 없음
  → `LEEjy0431` 계정 Personal Access Token으로 push
  ```bash
  git push https://LEEjy0431:<TOKEN>@github.com/LEEjy0431/capstone_music_ver2.git kts
  ```

---

## [Sprint 5] 2026-05-11 — Flutter 프론트엔드 구축 + CORS 전역화

### 완료 항목

**백엔드 수정**
- `backend/main.go`: `corsHandler` 최상위 미들웨어로 이동
  - `GET, POST, OPTIONS` 허용
  - `Authorization, Accept, Content-Type` 헤더 허용
  - OPTIONS preflight 즉시 204 응답
- `backend/handlers/analyze.go`: 내부 `corsMiddleware` 제거 (단순화)

**Flutter 앱 (`flutter_app/`) 신규 생성**

| 파일 | 역할 |
|------|------|
| `pubspec.yaml` | http, file_picker, provider, fl_chart, intl |
| `lib/main.dart` | 앱 진입점, 탭 셸, 다크/라이트 전환 |
| `lib/theme.dart` | 다크/라이트 금색(#F0B429) 테마 |
| `lib/models/record.dart` | ScoreDetail, Feedback, PracticeRecord |
| `lib/services/api_service.dart` | multipart POST, kIsWeb 분기 |
| `lib/providers/record_provider.dart` | ChangeNotifier 상태 관리 |
| `lib/pages/home_page.dart` | 점수 추이 그래프, 최근 기록 |
| `lib/pages/analysis_page.dart` | 파일 업로드, 언어 선택, 결과 카드 |
| `lib/pages/history_page.dart` | 검색, 기록 목록 |
| `lib/pages/stats_page.dart` | 요일별 연습 분포 막대 그래프 |
| `lib/pages/profile_page.dart` | 이름/목표 편집, 다크모드, 뱃지 |
| `lib/widgets/score_bar.dart` | 점수 진행 바 위젯 |
| `lib/widgets/feedback_card.dart` | GPT 피드백 카드 위젯 |
| `android/app/src/main/AndroidManifest.xml` | INTERNET, READ_MEDIA_AUDIO, usesCleartextTraffic |
| `web/index.html` | Flutter Web 진입점 |
| `flutter_app/README.md` | DFD, 실행 가이드, 트러블슈팅 |

**기타**
- `.gitignore` 머지 컨플릭트 해결, Python `lib/` 규칙 제거 (Flutter `lib/` 충돌 방지)
- `docs/` 폴더 신규: `TODO.md`, `PROGRESS.md`

### 주요 결정 사항
- **Flutter** 선택: 단일 코드베이스로 Web + Android 동시 지원
- **Provider** 상태 관리: 경량, flutter 공식 권장, Riverpod 대비 학습비용 낮음
- **file_picker**: Web(바이트 직접)과 Android(파일 경로) 모두 `withData: true`로 통일
- API_BASE는 `--dart-define`으로 주입: 빌드 시점에 고정, 런타임 환경 분리

### 발생한 문제 & 해결
- `.gitignore`에 Python용 `lib/` 규칙이 있어 `flutter_app/lib/` 전체가 untracked 상태로 누락
  → `.gitignore`에서 `lib/` 제거, `git add -f flutter_app/lib/`으로 강제 추가
  → 이후 `.gitignore`에 `lib/` 없이 Flutter 전용 규칙만 추가

---

## [Sprint 6] 2026-05-22~28 — Mac 환경 호환성 + AI 피드백 SSE 분리 (session_id 방식)

### 완료 항목

**백엔드 — 채점/피드백 2단계 분리**

| 파일 | 변경 내용 |
|------|-----------|
| `backend/services/store.go` (신규) | `sync.Map` 기반 세션 스토어, TTL 5분 자동 만료 |
| `backend/models/types.go` | `AnalyzeResponse`에서 `Feedback` 제거, `SessionID` 추가 |
| `backend/handlers/analyze.go` | GPT 동기 호출 제거, `newSessionID()` + `StoreScore()` 추가 |
| `backend/handlers/feedback_stream.go` | 7개 score query param → `session_id` 단일 파라미터로 교체 |

**Flutter 앱 — session_id 방식 연동**

| 파일 | 변경 내용 |
|------|-----------|
| `flutter_app/lib/models/record.dart` | `feedback` nullable화, `sessionId` 필드 추가, `copyWith()` 추가 |
| `flutter_app/lib/services/feedback_stream_service.dart` | `stream()` 파라미터 `ScoreDetail` → `sessionId` 로 교체 |
| `flutter_app/lib/providers/record_provider.dart` | `updateFeedback(id, feedback)` 추가 |
| `flutter_app/lib/pages/analysis_page.dart` | `_streamFeedback(sessionId)` 방식으로 변경, `done` 시 provider 동기화 |

### 주요 결정 사항
- **Option A 채택**: `POST /api/analyze`는 채점 결과 + `session_id` 즉시 반환, GPT 피드백은 `GET /api/feedback/stream?session_id=<id>` SSE로 분리
  - 이유: Python 분석(~30초) 완료 즉시 점수 표시 후 피드백을 스트리밍으로 UX 개선
- **앱(Flutter) 전환 확정**: React 웹 프론트엔드 대신 Flutter 앱을 메인 클라이언트로 결정
  - 이유: Android + Web 단일 코드베이스, 모바일 UX 최적화
- **session_id 신뢰성 개선**: 서버에서 `crypto/rand` 16바이트 생성, TTL 5분 후 자동 폐기
  - 기존 방식(클라이언트가 score 값 직접 전달)의 조작 가능성 해결

### 발생한 문제 & 해결
- 로컬 git 프록시가 `kimtaesung98` 계정으로 고정 → LEEjy0431 레포 쓰기 권한 없음
  → `git push https://LEEjy0431:<TOKEN>@github.com/...` 방식으로 우회 (Sprint 4와 동일)
- 직접 URL push 후 로컬 `origin/kts` 트래킹 미갱신
  → `git fetch origin kts` 로 트래킹 동기화

### 다음 스프린트 예정
- Flutter Android APK 빌드 및 실기기 테스트
- `shared_preferences`로 분석 기록 로컬 저장
- `godotenv`로 `.env` 자동 로딩
- Docker Compose (Go + Python 통합 실행)

---

## [Sprint 7] 2026-05-28 — 로컬 저장소 + Docker + pytest

### 완료 항목

**Flutter — 로컬 저장소 (`shared_preferences`)**

| 파일 | 변경 내용 |
|------|-----------|
| `flutter_app/lib/models/record.dart` | `toJson()` 추가 (ScoreDetail, Feedback, PracticeRecord), `fromStoredJson()` 팩토리 추가 |
| `flutter_app/lib/services/storage_service.dart` | 신규 — SharedPreferences CRUD (`loadRecords` / `saveRecords`) |
| `flutter_app/lib/providers/record_provider.dart` | `init()` 앱 시작 로드, `analyze` / `updateFeedback` / `deleteRecord` 후 자동 저장 |
| `flutter_app/lib/main.dart` | `WidgetsFlutterBinding.ensureInitialized()` + `await provider.init()` 추가 |
| `flutter_app/lib/pages/history_page.dart` | `ExpansionTile` 피드백 인라인 표시 + 삭제 확인 다이얼로그 |

**Docker — Go + Python 통합 실행**

| 파일 | 변경 내용 |
|------|-----------|
| `Dockerfile` | 멀티스테이지: go-builder(1.24-alpine) → runtime(python:3.10-slim) |
| `docker-compose.yml` | 단일 서비스, env_file `.env`, healthcheck `/health` |
| `.dockerignore` | node_modules / .env / flutter_app 등 빌드 불필요 파일 제외 |

**Python — pytest 단위 테스트**

| 파일 | 변경 내용 |
|------|-----------|
| `code/tests/__init__.py` | 패키지 선언 |
| `code/tests/conftest.py` | `sys.path` 자동 설정 |
| `code/tests/test_module3.py` | `compare_notes` / `group_chords` 22개 테스트 (100% 통과) |
| `code/pytest.ini` | testpaths / python_files 설정 |
| `requirements-llm.txt` | `pytest>=8.0.0` 추가 |

### 주요 결정 사항
- **sessionId 저장 제외**: `shared_preferences`에 저장 시 `sessionId`는 TTL 5분이므로 제외. 재로드 후 피드백 재요청이 필요한 경우 UX에서 안내
- **단일 컨테이너 Docker**: Go subprocess → Python 방식 유지. 마이크로서비스 분리는 오버엔지니어링
- **pytest scope**: module3 (순수 로직)만 단위 테스트. module1(music21), module2(piano_transcription)는 무거운 모델 의존성으로 통합 테스트 대상

### 발생한 문제 & 해결
- 없음 (22개 테스트 전량 통과)

### 다음 스프린트 예정
- [ ] Flutter Android APK 실기기 테스트
- [ ] Docker 이미지 빌드 검증 (`docker compose build`)
- [ ] module1 통합 테스트 (MusicXML 샘플 파일 활용)
- [ ] 서버 배포 (Render / Railway / fly.io 등 무료 호스팅)
