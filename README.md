# 피아노 연주 자동 평가 시스템

피아노 악보(MusicXML)와 연주 음원(WAV)을 비교 분석하여 GPT 기반 다국어 피드백을 제공하는 **PWA(Progressive Web App)** 입니다.  
모바일 브라우저에서 "홈 화면에 추가"로 앱처럼 설치할 수 있습니다.

---

## 아키텍처 개요

```
브라우저 (PWA)
    │
    │  ① POST /api/analyze
    │    multipart: sheet(XML) + audio(WAV) + lang
    ▼
┌─────────────────────────────────────────────────────────┐
│                    Go 백엔드 서버                         │
│                                                          │
│  ┌─────────────────┐         ┌──────────────────────┐   │
│  │  1. 파일 수신    │         │  3. 채점 결과 전달    │   │
│  │  (analyze.go)   │         │  + session_id 생성   │   │
│  └────────┬────────┘         │  (store.go)          │   │
│           │ 임시 파일 저장    └──────────┬────────────┘  │
│           ▼                             │               │
│  ┌─────────────────┐                    │               │
│  │  2. Python 실행  │────────────────────┘               │
│  │ (python_runner) │  ScoreResult JSON                  │
│  └─────────────────┘                                    │
│                                                          │
│  정적 파일 서빙: dist/ → SPA 폴백 (static.go)            │
└─────────────────────────────────────────────────────────┘
    │ subprocess                  │ { score, grade, session_id }
    ▼                             ▼
┌─────────────────────────┐   PWA (점수 즉시 표시)
│   Python 분석 파이프라인  │       │
│                         │       │  ② GET /api/feedback/stream
│  module1.py             │       │    ?session_id=<id>&lang=ko
│  ┌───────────────────┐  │       ▼
│  │ MusicXML → 음표   │  │  ┌──────────────────────────────────┐
│  └────────┬──────────┘  │  │  Go 백엔드 서버                   │
│           ▼             │  │                                  │
│  module2.py             │  │  4. GetScore(session_id)         │
│  ┌───────────────────┐  │  │  5. GPT 피드백 생성 (SSE)        │
│  │ WAV → Piano 모델  │  │  │     (gpt_stream.go + i18n.go)   │
│  └────────┬──────────┘  │  │     event: chunk / done / error  │
│           ▼             │  └──────────────────────────────────┘
│  module3.py             │       │ SSE 스트리밍
│  ┌───────────────────┐  │       ▼
│  │ 음표 비교 & 채점   │  │   PWA (섹션 진행바 → 피드백 카드)
│  └───────────────────┘  │
└─────────────────────────┘
```

---

## 프로젝트 구조

```
capstone_music_ver2/
├── backend/                         # Go 백엔드 서버
│   ├── main.go                      # 서버 진입점, PWA dist/ 서빙
│   ├── go.mod
│   ├── handlers/
│   │   ├── analyze.go               # POST /api/analyze
│   │   ├── feedback_stream.go       # GET /api/feedback/stream (SSE)
│   │   └── static.go                # SPA 폴백 핸들러
│   ├── models/
│   │   └── types.go                 # ScoreResult, FeedbackResult 등
│   └── services/
│       ├── python_runner.go         # Python subprocess 실행
│       ├── store.go                 # session_id 메모리 저장 (TTL 5분)
│       ├── gpt.go                   # OpenAI GPT API (비스트리밍)
│       ├── gpt_stream.go            # OpenAI GPT API (SSE 스트리밍)
│       ├── i18n.go                  # 언어별 프롬프트 빌더
│       └── i18n_schema.go           # GPT JSON 스키마 (strict)
├── code/                            # Python 분석 파이프라인
│   ├── main.py                      # 파이프라인 진입점 (--json 모드)
│   ├── module1.py                   # MusicXML → 음표 추출 (music21)
│   ├── module2.py                   # WAV → 음표 추출 (piano_transcription)
│   ├── module3.py                   # 음표 비교 & 채점
│   └── tests/                       # pytest 단위 테스트 (22개)
├── src/                             # React PWA 프론트엔드
│   ├── App.jsx                      # 루트, localStorage, getApiBase()
│   ├── AnalysisPage.jsx             # 파일 업로드 + SSE 피드백 UI
│   ├── HomePage.jsx                 # 대시보드, 히트맵, 점수 추이
│   ├── HistoryPage.jsx              # 연습 기록 목록
│   ├── StatsPage.jsx                # 레이더 차트, 요일별 통계
│   └── ProfilePage.jsx              # 프로필, 서버 URL 설정
├── public/
│   └── icon.svg                     # PWA 아이콘
├── dist/                            # 빌드 결과물 (npm run build 생성)
├── netlify.toml                     # Netlify 배포 설정
├── render.yaml                      # Render 전체 스택 배포 설정
├── vite.config.js                   # Vite + VitePWA 설정
├── index.html                       # PWA 메타 태그 포함
├── .env.example                     # 환경변수 템플릿
├── package.json
├── requirements.txt                 # Python 의존성 (Windows/Linux)
├── requirements-mac.txt             # macOS 추가 의존성 (tensorflow-macos)
└── requirements-llm.txt             # OpenAI + pytest
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트엔드 | React 18, Vite, vite-plugin-pwa (PWA) |
| 백엔드 | Go 1.24 (net/http) |
| 음악 분석 | Python 3.10, music21, piano_transcription_inference |
| AI 피드백 | OpenAI GPT-4o-mini, SSE 스트리밍 |
| 상태 저장 | localStorage (기록/프로필), sync.Map TTL 5분 (session) |
| 배포 | Netlify (PWA) + Render (백엔드) 또는 Go 단일 서버 |
| 지원 언어 | 한국어, English, 日本語, 中文 |

---

## 시작 가이드

### 사전 요구사항

- **Go** 1.21 이상
- **Python** 3.10 이상
- **Node.js** 18 이상
- **OpenAI API Key** ([platform.openai.com](https://platform.openai.com) 발급)

---

### 1단계 — 저장소 클론

```bash
git clone https://github.com/LEEjy0431/capstone_music_ver2.git
cd capstone_music_ver2
git checkout kts
```

---

### 2단계 — 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 아래 두 항목을 입력합니다:

```env
OPENAI_API_KEY=sk-proj-...          # OpenAI API 키 (필수)
PROJECT_ROOT=/절대경로/capstone_music_ver2   # 프로젝트 루트 경로

# Python 실행 명령어 (기본값: python3)
# Mac Anaconda 사용 시 전체 경로 입력:
# PYTHON_CMD=/opt/homebrew/anaconda3/envs/capstone/bin/python
# Windows:
# PYTHON_CMD=python
```

---

### 3단계 — Python 의존성 설치

**macOS (Apple Silicon M1/M2/M3):**
```bash
pip install -r requirements.txt -r requirements-mac.txt -r requirements-llm.txt
```

**Windows / Linux:**
```bash
pip install -r requirements.txt -r requirements-llm.txt
pip install tensorflow==2.16.2   # tensorflow는 플랫폼별 별도 설치
```

> 가상환경 사용 권장:
> ```bash
> python -m venv venv
> source venv/bin/activate          # macOS/Linux
> venv\Scripts\activate             # Windows
> # 이후 위 pip install 명령어 실행
> ```

---

### 4단계 — Go 백엔드 서버 실행

```bash
cd backend
go run .
```

정상 실행 시:
```
.env 로딩: /path/to/capstone_music_ver2/.env
서버 시작: http://localhost:8080
```

헬스체크:
```bash
curl http://localhost:8080/health
# {"status":"ok"}
```

---

### 5단계 — PWA 프론트엔드 실행

**개발 서버 (핫리로드):**
```bash
npm install      # 최초 1회
npm run dev
# → http://localhost:5173
```

**프로덕션 빌드 (Go 서버가 함께 서빙):**
```bash
npm run build
# dist/ 생성 후 Go 서버(localhost:8080)에서 PWA 자동 서빙
```

---

### 6단계 — 서버 URL 연결 (개발 서버 사용 시)

1. 브라우저에서 `http://localhost:5173` 접속
2. **프로필 탭** → 서버 연결 → `http://localhost:8080` 입력
3. **연결 테스트** → "✓ 서버 연결 성공" 확인 → **저장**

> 프로덕션 빌드(`npm run build`) 후 Go 서버(8080)로 접속하면 서버 URL 설정 불필요

---

### 7단계 — 사용 방법

1. **분석 탭** → WAV 파일 + MusicXML 파일 업로드
2. 피드백 언어 선택 (한국어 / English / 日本語 / 中文)
3. **분석 시작하기** 클릭
4. 결과 확인:
   - 점수 및 등급 (A+~C) — **즉시 표시**
   - 정확도 / 누락 음표 / 박자 오류 바 차트
   - GPT 피드백 진행 바 → 피드백 카드 (종합 평가 / 음정 / 리듬 / 타이밍 / 개선 팁)

---

### PWA 설치 (모바일 홈 화면)

| OS | 방법 |
|----|------|
| iOS Safari | 공유 버튼 → "홈 화면에 추가" |
| Android Chrome | 주소창 설치 아이콘 또는 메뉴 → "앱 설치" |

---

### Python 파이프라인 단독 테스트

```bash
# 콘솔 출력 모드
python code/main.py --sheet data/piano_sheet_3.xml --audio data/piano_record_3.wav

# JSON 모드 (Go 연동과 동일)
python code/main.py --sheet data/piano_sheet_3.xml --audio data/piano_record_3.wav --json

# 단위 테스트
cd code && pytest tests/ -v
```

---

## API 명세

### `POST /api/analyze`

**Request** — `multipart/form-data`

| 필드 | 타입 | 설명 |
|------|------|------|
| `sheet` | File | 악보 파일 (MusicXML, .xml) |
| `audio` | File | 연주 음원 파일 (.wav) |
| `lang` | string | 피드백 언어 (`ko` / `en` / `ja` / `zh`), 기본값 `ko` |

**Response** — `application/json`

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

> GPT 피드백은 포함되지 않습니다. `session_id`로 `/api/feedback/stream` 에서 별도 수신합니다.

**등급 기준**

| 점수 | 등급 |
|------|------|
| 95점 이상 | A+ |
| 90점 이상 | A |
| 85점 이상 | A- |
| 80점 이상 | B+ |
| 75점 이상 | B |
| 70점 이상 | C+ |
| 70점 미만 | C |

---

### `GET /api/feedback/stream`

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `session_id` | string | `/api/analyze` 응답의 `session_id` (유효시간 5분) |
| `lang` | string | 피드백 언어, 기본값 `ko` |

**Response** — `text/event-stream` (SSE)

```
event: chunk
data: {"type":"chunk","text":"전반적으로 안정적인 연주입니다"}

event: done
data: {"type":"done","feedback":{"overall":"...","pitch":"...","rhythm":"...","timing":"...","tips":["...","..."],"encouragement":"..."}}

event: error
data: {"type":"error","error":"세션을 찾을 수 없습니다"}
```

---

### `GET /health`

```json
{"status": "ok"}
```

---

## 트러블슈팅

**`.env` 로딩 메시지가 안 보임**
→ 서버가 `backend/` 디렉토리에서 실행될 때 `../env`를 자동 탐색합니다. `PROJECT_ROOT` 를 명시하면 확실합니다:
```env
PROJECT_ROOT=D:\Projects\capstone_music_ver2   # Windows
PROJECT_ROOT=/Users/yourname/capstone_music_ver2  # macOS
```

**`OPENAI_API_KEY 미설정` 오류**
→ `.env` 파일에 키가 있는지, Go 서버가 프로젝트 루트에서 실행되는지 확인하세요.

**Python 실행 실패**
→ 가상환경이 활성화된 상태에서 Go 서버를 실행하거나 `.env`에 `PYTHON_CMD` 전체 경로를 설정하세요:
```env
PYTHON_CMD=/opt/homebrew/anaconda3/envs/capstone/bin/python
```

**macOS에서 `tensorflow` 설치 실패**
→ `requirements-mac.txt`를 함께 설치하세요:
```bash
pip install -r requirements.txt -r requirements-mac.txt -r requirements-llm.txt
```

**WAV 분석 실패**
→ 표준 PCM WAV 포맷인지 확인하세요. MP3는 변환 후 사용:
```bash
ffmpeg -i input.mp3 output.wav
```

**CORS 오류 (개발 서버)**
→ 프로필 탭 → 서버 연결에서 Go 서버 URL(`http://localhost:8080`)을 저장했는지 확인하세요.

---

## 폴더별 상세 문서

| 폴더 | 설명 | 문서 |
|------|------|------|
| `backend/` | Go HTTP 서버 | [backend/README.md](./backend/README.md) |
| `code/` | Python 분석 파이프라인 | [code/README.md](./code/README.md) |
| `src/` | React PWA 프론트엔드 | [src/README.md](./src/README.md) |
