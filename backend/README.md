# Backend — Go HTTP 서버

피아노 연주 분석 요청을 수신하고, Python 파이프라인 실행 및 OpenAI GPT 피드백 생성을 오케스트레이션하는 Go 백엔드 서버입니다.

---

## 폴더 구조

```
backend/
├── main.go                  # 서버 진입점, 라우팅
├── go.mod                   # Go 모듈 정의
├── handlers/
│   ├── analyze.go           # POST /api/analyze 핸들러 (채점 + session_id 반환)
│   └── feedback_stream.go   # GET /api/feedback/stream 핸들러 (SSE 피드백)
├── models/
│   └── types.go             # 공유 타입 정의
└── services/
    ├── python_runner.go     # Python subprocess 실행
    ├── store.go             # 세션 스토어 (sync.Map, TTL 5분)
    ├── gpt.go               # OpenAI API 동기 호출
    ├── gpt_stream.go        # OpenAI API SSE 스트리밍 호출
    ├── i18n.go              # 언어별 프롬프트 생성
    └── i18n_schema.go       # GPT JSON Schema (strict mode)
```

---

## DFD (Data Flow Diagram)

### Level 1 — 요청 처리 흐름 (2단계 분리)

```
Flutter 앱
    │
    │  ① POST /api/analyze
    │    multipart/form-data { sheet, audio, lang }
    ▼
┌──────────────────────────────────────────┐
│  handlers/analyze.go                     │
│                                          │
│  1. ParseMultipartForm()                 │
│  2. saveUploadedFile() → /tmp/           │
│  3. RunPythonAnalysis() → ScoreResult    │
│  4. newSessionID() + StoreScore()        │
│  5. calcGrade()                          │
│  6. AnalyzeResponse { score, grade,      │
│                       lang, session_id } │
└──────────────────────────────────────────┘
    │
    │  { score, grade, lang, session_id }
    ▼
Flutter 앱 (점수 즉시 표시)
    │
    │  ② GET /api/feedback/stream?session_id=<id>&lang=ko
    ▼
┌──────────────────────────────────────────┐
│  handlers/feedback_stream.go             │
│                                          │
│  1. GetScore(session_id) → ScoreResult   │
│     └─ 만료/미존재 시 404               │
│  2. GenerateFeedbackStream()             │
│     ├─ BuildFeedbackPrompt()             │
│     ├─ OpenAI stream: true               │
│     ├─ event: chunk  (텍스트 조각)       │
│     └─ event: done   (완성 JSON)         │
└──────────────────────────────────────────┘
    │
    │  SSE 스트리밍
    ▼
Flutter 앱 (피드백 실시간 표시)
```

### Level 2 — 데이터 타입 흐름

```
① POST /api/analyze
─────────────────────────────────────────────
multipart Form
    ├─[sheet: File] → os.CreateTemp("*.xml") → sheetPath
    ├─[audio: File] → os.CreateTemp("*.wav") → audioPath
    └─[lang: string] ─────────────────────── → lang

RunPythonAnalysis(sheetPath, audioPath)  →  ScoreResult {
    score, correct, total,
    missed_count, wrong_timing_count, extra_count,
    avg_timing_deviation, missed_notes[], ...
}

newSessionID()  →  "a3f8c2d1..." (crypto/rand 16바이트)
StoreScore(sessionID, ScoreResult)  →  메모리 저장 (TTL 5분)

AnalyzeResponse {
    score     ScoreResult
    grade     string    // A / A- / B+ / B / C+ / C
    lang      string
    session_id string   // 피드백 스트리밍에 사용
}

② GET /api/feedback/stream?session_id=<id>&lang=ko
─────────────────────────────────────────────
GetScore(sessionID)  →  ScoreResult (만료 시 404)

BuildFeedbackPrompt(score, lang)  →  system + user prompt
feedbackJSONSchema (strict)       →  OpenAI 구조화 출력 강제

SSE 이벤트 흐름:
    event: chunk  data: {"type":"chunk","text":"전반적으로..."}
    event: chunk  data: {"type":"chunk","text":"음정 정확도..."}
    event: done   data: {"type":"done","feedback":{
                      overall, pitch, rhythm, timing,
                      tips[], encouragement
                  }}
```

---

## 라이브러리 설치

### Go 런타임 설치

```bash
# macOS
brew install go

# Ubuntu / Debian
sudo apt install golang-go

# Windows — https://go.dev/dl/ 에서 설치 파일 다운로드

# 버전 확인 (1.21 이상 필요)
go version
```

### Go 모듈 의존성 설치

```bash
cd backend

# go.mod 에 정의된 모든 의존성 다운로드
go mod download

# 또는 빌드 시 자동 다운로드
go build ./...
```

### 의존성 목록 (`go.mod`)

| 패키지 | 역할 | 비고 |
|--------|------|------|
| `net/http` (표준 라이브러리) | HTTP 서버, 라우팅, multipart 파싱 | 외부 설치 불필요 |
| `encoding/json` (표준 라이브러리) | JSON 직렬화·역직렬화 | 외부 설치 불필요 |
| `os/exec` (표준 라이브러리) | Python subprocess 실행 | 외부 설치 불필요 |
| `bufio`, `strings` (표준 라이브러리) | SSE 스트림 파싱 | 외부 설치 불필요 |
| `log/slog` (표준 라이브러리) | 구조화 로깅 | Go 1.21+ 포함 |

> **외부 패키지 없음**: 이 서버는 Go 표준 라이브러리만 사용합니다.  
> OpenAI API는 `net/http` 로 직접 호출하므로 별도 SDK 불필요.

### OpenAI API 키 발급

1. `https://platform.openai.com/api-keys` 접속
2. `+ Create new secret key` 클릭
3. 키 복사 후 `.env` 파일에 저장:

```bash
cp .env.example .env
# .env 파일 편집
OPENAI_API_KEY=sk-...
```

### go.mod 초기화 (저장소 클론 후 최초 1회)

```bash
cd backend
go mod tidy   # 미사용 의존성 제거, 누락 의존성 추가
```

---

## 환경변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API 키 |
| `PORT` | | `8080` | 서버 포트 |
| `PROJECT_ROOT` | ✅ (`go run` 시) | — | 프로젝트 루트 절대 경로 |

> **PROJECT_ROOT 필요 이유**
> `go run` 실행 시 바이너리가 임시 디렉토리에 생성되어 `code/main.py` 경로를 자동 탐색할 수 없습니다.
> 컴파일된 바이너리(`go build`)는 `os.Executable()` 기반으로 자동 탐색합니다.

---

## 실행 방법

### 개발 (go run)

```bash
# Windows
set OPENAI_API_KEY=sk-...
set PROJECT_ROOT=D:\Projects\capstone_music_ver2
cd backend
go run main.go

# macOS / Linux
export OPENAI_API_KEY=sk-...
export PROJECT_ROOT=/path/to/capstone_music_ver2
cd backend
go run main.go
```

### 프로덕션 (go build)

```bash
cd backend
go build -o server main.go

# 실행 (PROJECT_ROOT 불필요)
OPENAI_API_KEY=sk-... ./server
```

---

## API 명세

### `POST /api/analyze`

**Request** — `multipart/form-data`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `sheet` | File | ✅ | 악보 파일 (MusicXML, `.xml`) |
| `audio` | File | ✅ | 연주 음원 파일 (`.wav`) |
| `lang` | string | | 피드백 언어 (`ko`/`en`/`ja`/`zh`), 기본값 `ko` |

**Response 200** — `application/json`

```json
{
  "score": {
    "score": 83.5,
    "correct": 67,
    "total": 80,
    "missed_count": 8,
    "wrong_timing_count": 5,
    "extra_count": 2,
    "avg_timing_deviation": 0.087
  },
  "grade": "B+",
  "lang": "ko",
  "session_id": "a3f8c2d1e4b5f6a7b8c9d0e1f2a3b4c5"
}
```

> `session_id` 는 5분간 유효합니다. 이 값을 `GET /api/feedback/stream` 에 전달하세요.

**Response 4xx / 5xx**

```json
{ "error": "오류 메시지" }
```

---

### `GET /api/feedback/stream`

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `session_id` | string | ✅ | `POST /api/analyze` 응답의 `session_id` (유효시간 5분) |
| `lang` | string | | 피드백 언어 (`ko`/`en`/`ja`/`zh`), 기본값 `ko` |

**Response** — `text/event-stream` (SSE)

```
event: chunk
data: {"type":"chunk","text":"전반적으로 안정적인 연주입니다"}

event: chunk
data: {"type":"chunk","text":"..."}

event: done
data: {"type":"done","feedback":{"overall":"...","pitch":"...","rhythm":"...","timing":"...","tips":["..."],"encouragement":"..."}}
```

**오류 응답**

```
event: error
data: {"type":"error","error":"세션을 찾을 수 없습니다 (만료되었거나 존재하지 않음)"}
```

---

### `GET /health`

```json
{ "status": "ok" }
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `OPENAI_API_KEY 환경변수가 설정되지 않았습니다` | 환경변수 누락 | `export OPENAI_API_KEY=sk-...` 설정 |
| `python 실행 실패: ...` | Python 미설치 또는 의존성 누락 | `pip install -r requirements.txt -r requirements-llm.txt` |
| `결과 JSON 파싱 실패` | Python 모듈이 stdout에 오류 출력 | stderr 확인: `cmd.Stderr` 로그 참고 |
| `PROJECT_ROOT` 관련 경로 오류 | `go run` 시 환경변수 미설정 | `export PROJECT_ROOT=<프로젝트 루트>` 설정 |
