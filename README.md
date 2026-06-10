# 피아노 연주 자동 평가 시스템

피아노 악보(MusicXML/PDF/이미지)와 연주 음원(WAV)을 비교 분석하여 AI 기반 피드백을 제공하는 **PWA(Progressive Web App)** 입니다.  
모바일 브라우저에서 "홈 화면에 추가"로 앱처럼 설치할 수 있습니다.

---

## 아키텍처 개요

```
브라우저 (PWA)
    │
    │  ① POST /api/analyze
    │    multipart: sheet(XML/PDF/이미지) + audio(WAV)
    ▼
┌─────────────────────────────────────────────────────────┐
│                    Go 백엔드 서버                         │
│                                                          │
│  ┌─────────────────┐         ┌──────────────────────┐   │
│  │  1. 파일 수신    │         │  3. 채점 결과 저장    │   │
│  │  (analyze.go)   │         │  + session_id 생성   │   │
│  └────────┬────────┘         │  (store.go, TTL 5분) │   │
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
┌────────────────────────────┐  PWA (점수 즉시 표시)
│   Python 분석 파이프라인    │       │
│                            │       │  ② GET /api/feedback/stream
│  module1.py                │       │    ?session_id=<id>
│  ┌─────────────────────┐   │       ▼
│  │ MusicXML → 음표     │   │  ┌──────────────────────────────────┐
│  │ (music21 + Audiveris│   │  │  Go 백엔드 서버                   │
│  │  PDF/이미지 지원)   │   │  │                                  │
│  └──────────┬──────────┘   │  │  4. GetScore(session_id)         │
│             ▼              │  │  5. AI 피드백 생성 (SSE)          │
│  module2.py                │  │     (gpt_stream.go)             │
│  ┌─────────────────────┐   │  │     OpenAI GPT-4o-mini          │
│  │ WAV → Piano 모델    │   │  │     또는 Ollama (로컬 LLM)      │
│  │ (piano_transcription│   │  │     event: chunk/done/error     │
│  │  _inference)        │   │  └──────────────────────────────────┘
│  └──────────┬──────────┘   │       │ SSE 스트리밍
│             ▼              │       ▼
│  module3.py                │   PWA (진행 바 → 피드백 카드)
│  ┌─────────────────────┐   │
│  │ 음표 비교 & 채점     │   │
│  └──────────┬──────────┘   │
│             ▼              │
│  chord_upgrade.py          │
│  ┌─────────────────────┐   │
│  │ CQT 기반 누락 음표  │   │
│  │ 화음 재검증         │   │
│  └─────────────────────┘   │
└────────────────────────────┘
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
│       ├── gpt.go                   # OpenAI / Ollama API (비스트리밍)
│       ├── gpt_stream.go            # OpenAI / Ollama API (SSE 스트리밍)
│       ├── i18n.go                  # 피드백 프롬프트 빌더 (한국어 고정)
│       └── i18n_schema.go           # GPT JSON 스키마
├── code/                            # Python 분석 파이프라인
│   ├── main.py                      # 파이프라인 진입점 (--json 모드)
│   ├── module1.py                   # 악보 → 음표 추출 (music21, Audiveris)
│   ├── module2.py                   # WAV → 음표 추출 (piano_transcription_inference)
│   ├── module3.py                   # 음표 비교 & 채점
│   ├── chord_upgrade.py             # CQT 기반 화음 재검증 (누락 음표 보완)
│   ├── environment.yml              # Anaconda 환경 정의
│   └── tests/                       # pytest 단위 테스트 (22개)
│       ├── conftest.py
│       └── test_module3.py
├── src/                             # React PWA 프론트엔드
│   ├── App.jsx                      # 루트, localStorage, getApiBase()
│   ├── AnalysisPage.jsx             # 파일 업로드 + SSE 피드백 UI
│   ├── HomePage.jsx                 # 대시보드, 히트맵, 점수 추이
│   ├── HistoryPage.jsx              # 연습 기록 목록
│   ├── StatsPage.jsx                # 레이더 차트, 요일별 통계
│   └── ProfilePage.jsx              # 프로필, 서버 URL 설정
├── flutter_app/                     # Flutter 앱 (레거시 — Web/Android)
│   └── lib/                         # pages, services, providers, models
├── data/                            # 테스트용 샘플 파일
│   ├── *.xml                        # MusicXML 악보 샘플
│   └── *.wav                        # 연주 음원 샘플
├── docs/                            # 개발 문서
│   ├── PROGRESS.md                  # Sprint별 개발 기록
│   ├── GUIDE_MAC.md                 # macOS 개발 환경 가이드
│   └── TODO.md                      # 미완료 항목
├── public/
│   └── icon.svg                     # PWA 아이콘 (피아노 건반 + 금색 음표)
├── piano_transcription_inference_data/
│   └── note_F1=0.9677_pedal_F1=0.9186.pth  # 사전학습 모델 가중치
├── netlify.toml                     # Netlify 배포 설정
├── render.yaml                      # Render 전체 스택 배포 설정
├── vite.config.js                   # Vite + VitePWA 설정
├── index.html                       # PWA 메타 태그 포함
├── .env.example                     # 환경변수 템플릿
├── package.json
├── requirements.txt                 # Python 공통 의존성
├── requirements-mac.txt             # macOS 추가 의존성 (tensorflow-macos)
└── requirements-llm.txt             # OpenAI + pytest
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트엔드 | React 19, Vite 8, vite-plugin-pwa (PWA) |
| 백엔드 | Go 1.24 (net/http) |
| 악보 분석 | Python 3.10+, music21, Audiveris (PDF/이미지 → MusicXML) |
| 음표 추출 | piano_transcription_inference (LSTM 기반 피아노 특화 모델) |
| 화음 재검증 | librosa CQT (Constant-Q Transform) |
| AI 피드백 | OpenAI GPT-4o-mini 또는 Ollama (Qwen 2.5-1.5B, 로컬 실행) |
| SSE 스트리밍 | Go `text/event-stream`, React `ReadableStream` |
| 상태 저장 | localStorage (기록/프로필), sync.Map TTL 5분 (session) |
| 테스트 | pytest (22개 단위 테스트) |
| 배포 | Netlify (PWA) + Render (백엔드) 또는 Go 단일 서버 |
| 피드백 언어 | 한국어 (고정) |

---

## 채점 알고리즘

```
1. module1: 악보(MusicXML/PDF/이미지) → 기준 음표 리스트 추출
   - 꾸밈음(grace note), 중복 음표 제거로 정확도 개선
   - PDF/이미지는 Audiveris로 MusicXML 자동 변환

2. module2: WAV → 연주 음표 리스트 추출
   - piano_transcription_inference (note F1=0.9677)
   - pre-roll padding으로 첫 음 누락 방지
   - velocity < 30, duration < 0.03s 필터링

3. module3: 음표 비교 & 채점
   - 글로벌 타이밍 오프셋 추정 (중앙값 기반)
   - onset_tolerance = 0.15s (기본)
   - wide_tolerance = 0.40s (옥타브 구제, 서스테인 매칭)
   - score = correct / total × 100

4. chord_upgrade: CQT 기반 화음 재검증
   - 채점에서 놓친(missed) 음표를 CQT 에너지로 재확인
   - 화음 구성음 누락을 줄여 점수 정확도 향상
```

### 등급 기준

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

## 시작 가이드

### 사전 요구사항

- **Go** 1.21 이상
- **Python** 3.10 이상 (Anaconda 권장)
- **Node.js** 18 이상
- **OpenAI API Key** 또는 **Ollama** 로컬 서버 (둘 중 하나)

macOS 상세 환경 설정: [`docs/GUIDE_MAC.md`](./docs/GUIDE_MAC.md)

---

### 1단계 — 저장소 클론

```bash
git clone https://github.com/LEEjy0431/capstone_music_ver2.git
cd capstone_music_ver2
git checkout leejy_mac
```

---

### 2단계 — 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 편집합니다:

```env
# AI 피드백 백엔드 (OpenAI 또는 Ollama 중 하나 선택)

# ── 옵션 A: OpenAI (권장) ─────────────────────────────────────
OPENAI_API_KEY=sk-proj-...

# ── 옵션 B: Ollama 로컬 LLM (무료, 인터넷 불필요) ──────────────
# Ollama 설치 후: ollama pull qwen2.5:1.5b
# OLLAMA_MODEL=qwen2.5:1.5b
# OLLAMA_URL=http://localhost:11434   # 기본값, 생략 가능

# ── 공통 설정 ─────────────────────────────────────────────────
PROJECT_ROOT=/절대경로/capstone_music_ver2
PORT=8080

# Python 실행 명령어 (Anaconda 환경 예시)
# PYTHON_CMD=/opt/homebrew/anaconda3/envs/capstone_music/bin/python
```

---

### 3단계 — Python 의존성 설치

**macOS (Apple Silicon M1/M2/M3) — Anaconda 권장:**

```bash
# 환경 생성 (최초 1회)
CONDA_SUBDIR=osx-arm64 conda env create -f code/environment.yml
conda activate capstone_music

# macOS 전용 TensorFlow (tensorflow → tensorflow-macos 교체)
pip uninstall tensorflow -y
pip install tensorflow-macos==2.16.2
pip install tensorflow-metal       # GPU 가속 (선택)
```

**Windows / Linux:**

```bash
pip install -r requirements.txt -r requirements-llm.txt
```

> Anaconda 환경 업데이트 (environment.yml 변경 후):
> ```bash
> conda env update -f code/environment.yml --prune
> ```

---

### 4단계 — Go 백엔드 서버 실행

```bash
# conda 환경이 활성화된 상태에서 실행 (python 경로 인식)
conda activate capstone_music

cd backend
go run main.go
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
# dist/ 생성 → Go 서버(localhost:8080)에서 PWA 자동 서빙
```

---

### 6단계 — 서버 URL 연결 (개발 서버 사용 시)

1. 브라우저에서 `http://localhost:5173` 접속
2. **프로필 탭** → 서버 연결 → `http://localhost:8080` 입력
3. **연결 테스트** 클릭 → "✓ 서버 연결 성공" 확인 → **저장**

> 프로덕션 빌드(`npm run build`) 후 Go 서버(8080)로 접속하면 서버 URL 설정 불필요

---

### 7단계 — 사용 방법

1. **분석 탭** → 악보 파일 + WAV 파일 업로드
   - 악보: `.xml` / `.musicxml` / `.mxl` / `.mid` / `.midi` / `.pdf` / `.png` / `.jpg` / `.jpeg`
   - 연주: `.wav`
2. **분석 시작하기** 클릭
3. 결과 확인 (채점 최대 20분 소요 — CPU 환경 기준):
   - 점수 및 등급 (A+~C) — **즉시 표시**
   - 정확도 / 누락 음표 / 박자 오류 바 차트
   - AI 피드백 스트리밍 → 피드백 카드
     - 종합 평가 / 음정 정확도 / 리듬 / 타이밍 / 개선 팁 / 마무리

---

### Ollama 로컬 LLM 설정 (선택)

OpenAI API 키 없이 무료로 AI 피드백을 받을 수 있습니다.

```bash
# Ollama 설치 (macOS)
brew install ollama

# 모델 다운로드 (약 1GB)
ollama pull qwen2.5:1.5b

# Ollama 서버 실행 (백그라운드)
ollama serve
```

`.env`에서 `OPENAI_API_KEY` 대신 `OLLAMA_MODEL` 설정:
```env
OLLAMA_MODEL=qwen2.5:1.5b
```

> OpenAI와 Ollama가 모두 설정된 경우 `OLLAMA_MODEL` 우선 사용

---

### PWA 설치 (모바일 홈 화면)

| OS | 방법 |
|----|------|
| iOS Safari | 공유 버튼 → "홈 화면에 추가" |
| Android Chrome | 주소창 설치 아이콘 또는 메뉴 → "앱 설치" |

---

### Python 파이프라인 단독 테스트

```bash
conda activate capstone_music

# 콘솔 출력 모드
python code/main.py --sheet data/piano_sheet_3.xml --audio data/piano_record_3.wav

# JSON 모드 (Go 연동과 동일)
python code/main.py --sheet data/piano_sheet_3.xml --audio data/piano_record_3.wav --json

# 단위 테스트 (22개, module3 순수 로직)
cd code && pytest tests/ -v
```

---

## API 명세

### `POST /api/analyze`

**Request** — `multipart/form-data`

| 필드 | 타입 | 설명 |
|------|------|------|
| `sheet` | File | 악보 파일 (MusicXML / PDF / 이미지 / MIDI) |
| `audio` | File | 연주 음원 파일 (.wav) |

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
  "session_id": "a3f8c2d1e4b5f6a7b8c9d0e1f2a3b4c5"
}
```

> GPT 피드백은 포함되지 않습니다. `session_id`로 `/api/feedback/stream`에서 별도 수신합니다.

---

### `GET /api/feedback/stream`

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `session_id` | string | `/api/analyze` 응답의 `session_id` (유효시간 5분) |

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

### 채점이 너무 오래 걸림 / 멈춰 보임

CPU 환경에서 `piano_transcription_inference` 모델 실행은 **5~20분** 소요됩니다.  
진행 상황 메시지(경과 시간)가 표시되면 정상입니다. 화면을 닫지 마세요.

이전 채점이 백그라운드에서 살아있는 경우 충돌이 발생할 수 있습니다:
```bash
# 막힌 프로세스 확인 및 종료
ps aux | grep "main.py" | grep -v grep
kill <PID>
```

---

### `OPENAI_API_KEY 미설정` / `OLLAMA_MODEL 미설정` 오류

→ `.env` 파일에 `OPENAI_API_KEY` 또는 `OLLAMA_MODEL` 중 하나가 설정되어 있는지 확인하세요.

---

### Python 실행 실패 (`python3: command not found`)

→ conda 환경이 활성화된 상태에서 Go 서버를 실행하거나, `.env`에 전체 경로를 설정하세요:
```env
PYTHON_CMD=/opt/homebrew/anaconda3/envs/capstone_music/bin/python
```

---

### macOS에서 `tensorflow` 설치 실패 (Apple Silicon)

```bash
pip uninstall tensorflow tensorflow-macos -y
pip install tensorflow-macos==2.16.2
pip install tensorflow-metal
```

---

### `piano_transcription_inference` 설치 오류

```bash
conda activate capstone_music
pip install piano-transcription-inference==0.0.6
```

---

### WAV 분석 실패

→ 표준 PCM WAV 포맷인지 확인하세요. MP3나 다른 형식은 변환 후 사용:
```bash
ffmpeg -i input.mp3 output.wav
```

---

### CORS 오류 (개발 서버)

→ 프로필 탭 → 서버 연결에서 Go 서버 URL(`http://localhost:8080`)을 저장했는지 확인하세요.

---

### `PROJECT_ROOT` 경로 오류

```bash
# 절대 경로로 설정 (상대 경로 사용 금지)
export PROJECT_ROOT=/Users/$(whoami)/capstone_music_ver2
```

---

## 빌드 상태

| 항목 | 결과 |
|------|------|
| Go build (`go build ./...`) | ✅ |
| PWA build (`npm run build`) | ✅ (246KB, gzip 70KB) |
| pytest (`code/tests/`) | ✅ 22/22 |

---

## 폴더별 상세 문서

| 폴더 | 문서 |
|------|------|
| `backend/` | [backend/README.md](./backend/README.md) |
| `code/` | [code/README.md](./code/README.md) |
| `src/` | [src/README.md](./src/README.md) |
| macOS 환경 가이드 | [docs/GUIDE_MAC.md](./docs/GUIDE_MAC.md) |
| 개발 진행 기록 | [docs/PROGRESS.md](./docs/PROGRESS.md) |
