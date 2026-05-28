# Backend — Go HTTP 서버

피아노 연주 분석 요청을 수신하고, Python 파이프라인 실행 및 OpenAI GPT 피드백 SSE 스트리밍을 오케스트레이션하는 Go 백엔드 서버입니다.

---

## 폴더 구조

```
backend/
├── main.go                      # 서버 진입점, 라우팅, godotenv 로드
├── go.mod                       # Go 모듈 정의
├── handlers/
│   ├── analyze.go               # POST /api/analyze — 채점만 수행
│   └── feedback_stream.go       # GET /api/feedback/stream — GPT SSE
├── models/
│   └── types.go                 # 공유 타입 정의
└── services/
    ├── python_runner.go         # Python subprocess 실행 (PYTHON_CMD 지원)
    ├── gpt_stream.go            # OpenAI SSE 스트리밍
    ├── gpt.go                   # OpenAI 공통 유틸
    ├── i18n.go                  # 언어별 프롬프트 생성
    └── i18n_schema.go           # JSON Schema strict 정의
```

---

## DFD (Data Flow Diagram)

### Level 1 — 2단계 분리 흐름

```
Flutter App
    │
    │  POST /api/analyze          (Step 1 — Python 채점, ~10~30s)
    │  multipart/form-data
    │  { sheet: File, audio: File, lang: string }
    ▼
┌──────────────────────────────────────────────────────────────┐
│  handlers/analyze.go                                         │
│                                                              │
│  1. ParseMultipartForm()                                     │
│     ├─ sheet  → saveUploadedFile() → /tmp/xxx.xml            │
│     └─ audio  → saveUploadedFile() → /tmp/xxx.wav            │
│                                                              │
│  2. services.RunPythonAnalysis(sheetPath, audioPath)         │
│  3. calcGrade(score.Score)                                   │
│  4. json.Encode(AnalyzeResponse)                             │
└──────────────────────────────────────────────────────────────┘
                    │
        ┌───────────▼────────────┐
        │  python_runner.go      │
        │                        │
        │  pythonBin()           │
        │  └─ PYTHON_CMD env     │   ← Mac conda 경로 설정 가능
        │     또는 python3       │
        │                        │
        │  context.WithTimeout   │   ← 5분 타임아웃
        │  exec.CommandContext(  │
        │   python main.py       │
        │   --sheet --audio      │
        │   --json               │
        │  )                     │
        │                        │
        │  stdout → JSON 파싱    │
        │  → ScoreResult         │
        └────────────────────────┘
                    │
                    ▼
        AnalyzeResponse { score, grade, lang }
                    │
                    ▼
            Flutter App (점수 카드 즉시 표시)
                    │
                    │  GET /api/feedback/stream   (Step 2 — GPT SSE, ~1~5s)
                    │  ?score=...&lang=ko
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  handlers/feedback_stream.go                                 │
│                                                              │
│  SSE 헤더 설정 (text/event-stream)                          │
│  services.GenerateFeedbackStream(w, score, lang)             │
└──────────────────────────────────────────────────────────────┘
                    │
        ┌───────────▼────────────┐
        │  gpt_stream.go         │
        │                        │
        │  BuildFeedbackPrompt() │
        │  OpenAI stream: true   │
        │  model: gpt-4o-mini    │
        │  response_format:      │
        │    json_schema strict  │
        │                        │
        │  bufio.Scanner 청크    │
        │  Flush() per chunk     │
        │                        │
        │  event: chunk → 토큰  │
        │  event: done  → JSON  │
        │  event: error → 오류  │
        └────────────────────────┘
                    │
                    ▼
            Flutter App (스트리밍 텍스트 → 완성 피드백 카드)
```

### Level 2 — 데이터 타입 흐름

```
Step 1 — POST /api/analyze
multipart Form
    │
    ├─[sheet: File]──► os.CreateTemp("*.xml") ──► sheetPath (string)
    ├─[audio: File]──► os.CreateTemp("*.wav") ──► audioPath (string)
    └─[lang: string]─────────────────────────────► lang (string)
           │
           ▼
  RunPythonAnalysis(sheetPath, audioPath)
           │
           │  stdout (JSON)
           ▼
  ScoreResult {
    score               float64   // 0~100점
    correct             int       // 정확히 연주한 음표 수
    total               int       // 전체 음표 수
    missed_count        int       // 누락 음표 수
    wrong_timing_count  int       // 박자 오류 수
    extra_count         int       // 추가 음표 수
    avg_timing_deviation float64  // 평균 타이밍 편차(초)
  }
           │
           ▼
  AnalyzeResponse { score, grade, lang }   ← feedback 없음

Step 2 — GET /api/feedback/stream (SSE)
Query: score, correct, total, missed, timing_errors, extra, avg_dev, lang
           │
           ▼
  GenerateFeedbackStream(w, score, lang)
           │  SSE events
           ├─ event: chunk  data: "토큰..."
           ├─ event: chunk  data: "토큰..."
           │  ...
           └─ event: done   data: { overall, pitch, rhythm, timing, tips[], encouragement }
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
| `github.com/joho/godotenv` | `.env` 파일 자동 로드 | `go get github.com/joho/godotenv` |

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
| `PROJECT_ROOT` | | — | 프로젝트 루트 절대 경로 (`go run` 시 권장) |
| `PYTHON_CMD` | | `python3` | Python 실행 명령어 (Mac conda 환경에서 전체 경로 지정) |

> **godotenv 자동 로드**: 서버 시작 시 `PROJECT_ROOT/.env` → `.env` → `../.env` 순서로 자동 탐색합니다.

> **PYTHON_CMD 설정 이유**: Mac Anaconda 환경에서는 시스템 `python3`이 아닌 conda 환경의 Python을 사용해야 합니다.
> `which python` (conda 활성화 후) 결과값을 `PYTHON_CMD`에 설정하세요.

---

## 실행 방법

### .env 파일 설정 (최초 1회)

```bash
cp .env.example .env
# 텍스트 편집기로 .env 열고 값 입력
```

### 개발 (go run)

```bash
# Mac / Linux
cd backend
go run main.go

# Windows
cd backend
go run main.go
```

### 프로덕션 (go build)

```bash
cd backend
go build -o server main.go
./server
```

### Mac Anaconda 환경 설정 예시

```bash
# 1. conda 환경 활성화
conda activate capstone

# 2. Python 경로 확인
which python   # 예: /opt/homebrew/anaconda3/envs/capstone/bin/python

# 3. .env 파일에 추가
echo "PYTHON_CMD=/opt/homebrew/anaconda3/envs/capstone/bin/python" >> .env
echo "PROJECT_ROOT=$(pwd)/.." >> .env

# 4. 서버 실행
cd backend
go run main.go
```

---

## API 명세

### `POST /api/analyze`

채점만 수행 (Python 파이프라인). GPT 피드백은 포함되지 않습니다.

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
  "lang": "ko"
}
```

### `GET /api/feedback/stream`

GPT 피드백을 SSE(Server-Sent Events)로 스트리밍합니다.

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `score` | float | 총점 (0~100) |
| `correct` | int | 정확히 연주한 음표 수 |
| `total` | int | 전체 음표 수 |
| `missed` | int | 누락 음표 수 |
| `timing_errors` | int | 박자 오류 수 |
| `extra` | int | 추가 음표 수 |
| `avg_dev` | float | 평균 타이밍 편차(초) |
| `lang` | string | 피드백 언어 (`ko`/`en`/`ja`/`zh`) |

**SSE Events**

```
event: chunk
data: "AI가 생성 중인 텍스트 토큰..."

event: done
data: {"overall":"...","pitch":"...","rhythm":"...","timing":"...","tips":["..."],"encouragement":"..."}

event: error
data: "오류 메시지"
```

### `GET /health`

```json
{ "status": "ok" }
```

**Response 4xx / 5xx**

```json
{ "error": "오류 메시지" }
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `OPENAI_API_KEY 환경변수가 설정되지 않았습니다` | 환경변수 누락 | `.env` 파일에 `OPENAI_API_KEY=sk-...` 추가 |
| `python 실행 실패: ...` | Python 미설치 또는 의존성 누락 | `PYTHON_CMD` 환경변수로 전체 경로 지정 |
| `결과 JSON 파싱 실패` | Python 모듈이 stdout에 오류 출력 | `code/` 폴더 의존성 설치 확인 (`pip install -r requirements.txt`) |
| `PROJECT_ROOT` 관련 경로 오류 | `go run` 시 환경변수 미설정 | `.env`에 `PROJECT_ROOT=<프로젝트 루트>` 추가 |
| Mac에서 `python3: command not found` | conda 환경 비활성화 | `conda activate capstone` 후 `PYTHON_CMD` 경로 설정 |
| SSE 스트리밍이 끊김 | 네트워크 프록시 또는 버퍼링 | `Connection: keep-alive` 헤더 확인, 프록시 비활성화 |
