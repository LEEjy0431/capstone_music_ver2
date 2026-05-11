# Backend — Go HTTP 서버

피아노 연주 분석 요청을 수신하고, Python 파이프라인 실행 및 OpenAI GPT 피드백 생성을 오케스트레이션하는 Go 백엔드 서버입니다.

---

## 폴더 구조

```
backend/
├── main.go                  # 서버 진입점, 라우팅
├── go.mod                   # Go 모듈 정의
├── handlers/
│   └── analyze.go           # POST /api/analyze 핸들러
├── models/
│   └── types.go             # 공유 타입 정의
└── services/
    ├── python_runner.go     # Python subprocess 실행
    ├── gpt.go               # OpenAI API 호출
    └── i18n.go              # 언어별 프롬프트 생성
```

---

## DFD (Data Flow Diagram)

### Level 1 — 요청 처리 흐름

```
Client (React)
    │
    │  POST /api/analyze
    │  multipart/form-data
    │  { sheet: File, audio: File, lang: string }
    ▼
┌──────────────────────────────────────────────────────────────┐
│  handlers/analyze.go                                         │
│                                                              │
│  1. ParseMultipartForm()                                     │
│     ├─ sheet  → saveUploadedFile() → /tmp/xxx.xml            │
│     ├─ audio  → saveUploadedFile() → /tmp/xxx.wav            │
│     └─ lang   → "ko" | "en" | "ja" | "zh"                   │
│                                                              │
│  2. services.RunPythonAnalysis(sheetPath, audioPath)   ──┐   │
│  3. services.GenerateFeedback(score, lang)             ──┤   │
│  4. calcGrade(score.Score)                                │   │
│  5. json.Encode(AnalyzeResponse)                          │   │
└───────────────────────────────────────────────────────────┼──┘
                                                            │
                    ┌───────────────────────────────────────┘
                    │
        ┌───────────▼────────────┐    ┌────────────────────────┐
        │  python_runner.go      │    │  gpt.go + i18n.go      │
        │                        │    │                        │
        │  projectRoot()         │    │  BuildFeedbackPrompt() │
        │  └─ PROJECT_ROOT env   │    │  └─ lang → system/user │
        │     또는 os.Executable │    │     prompt 생성        │
        │                        │    │                        │
        │  exec.Command(         │    │  OpenAI API 호출       │
        │   python3 main.py      │    │  model: gpt-4o-mini    │
        │   --sheet --audio      │    │  response_format: JSON │
        │   --json               │    │                        │
        │  )                     │    │  FeedbackResult 파싱   │
        │                        │    │  { overall, pitch,     │
        │  stdout → JSON 파싱    │    │    rhythm, timing,     │
        │  → ScoreResult         │    │    tips[], encourage } │
        └────────────────────────┘    └────────────────────────┘
                    │                              │
                    └──────────────┬───────────────┘
                                   ▼
                           AnalyzeResponse
                    { score, feedback, grade, lang }
                                   │
                                   ▼
                            Client (React)
```

### Level 2 — 데이터 타입 흐름

```
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
    missed_notes        []any
    wrong_timing_notes  []any
    extra_notes         []any
  }
           │
           ▼
  GenerateFeedback(score, lang)
           │
           │  OpenAI API
           ▼
  FeedbackResult {
    overall        string
    pitch          string
    rhythm         string
    timing         string
    tips           []string
    encouragement  string
  }
           │
           ▼
  AnalyzeResponse {
    score    ScoreResult
    feedback FeedbackResult
    grade    string    // A / A- / B+ / B / C+ / C
    lang     string
  }
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
  "feedback": {
    "overall": "...",
    "pitch": "...",
    "rhythm": "...",
    "timing": "...",
    "tips": ["...", "...", "..."],
    "encouragement": "..."
  },
  "grade": "B+",
  "lang": "ko"
}
```

**Response 4xx / 5xx**

```json
{ "error": "오류 메시지" }
```

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
