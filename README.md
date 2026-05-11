# 피아노 연주 자동 평가 시스템

피아노 악보(MusicXML)와 연주 음원(WAV)을 비교 분석하여 GPT 기반 다국어 피드백을 제공하는 모바일 웹 애플리케이션입니다.

---

## DFD (Data Flow Diagram)

### Level 0 — 컨텍스트 다이어그램

```
                        ┌─────────────────────────────┐
  악보 파일 (XML) ──────►│                             │
  음원 파일 (WAV) ──────►│   피아노 연주 평가 시스템    │──────► 점수 + GPT 피드백
  언어 선택 (lang) ─────►│                             │
                        └─────────────────────────────┘
```

---

### Level 1 — 주요 프로세스 흐름

```
사용자 (Browser)
    │
    │  POST /api/analyze
    │  multipart: sheet(XML) + audio(WAV) + lang
    ▼
┌─────────────────────────────────────────────────────────┐
│                    Go 백엔드 서버                        │
│                                                         │
│  ┌─────────────────┐         ┌──────────────────────┐  │
│  │  1. 파일 수신    │         │  4. GPT 피드백 생성   │  │
│  │  (analyze.go)   │         │  (gpt.go + i18n.go)  │  │
│  └────────┬────────┘         └──────────┬───────────┘  │
│           │ 임시 파일 저장               │ OpenAI API   │
│           ▼                             ▲              │
│  ┌─────────────────┐         ┌──────────┴───────────┐  │
│  │  2. Python 실행  │         │  3. 채점 결과 전달    │  │
│  │ (python_runner) │────────►│  ScoreResult JSON    │  │
│  └─────────────────┘         └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
    │                                       │
    │ subprocess 실행                        │ JSON 응답
    ▼                                       ▼
┌─────────────────────────────┐       사용자 (Browser)
│     Python 분석 파이프라인   │       score + feedback + grade
│                             │
│  module1.py                 │
│  ┌─────────────────────┐    │
│  │ MusicXML 파싱       │    │
│  │ → 정답 음표 추출     │    │
│  └──────────┬──────────┘    │
│             │               │
│  module2.py ▼               │
│  ┌─────────────────────┐    │
│  │ WAV → Piano 모델    │    │
│  │ → 연주 음표 추출     │    │
│  └──────────┬──────────┘    │
│             │               │
│  module3.py ▼               │
│  ┌─────────────────────┐    │
│  │ 음표 비교 & 채점     │    │
│  │ → score / missed /  │    │
│  │   timing_error 등   │    │
│  └─────────────────────┘    │
└─────────────────────────────┘
```

---

### Level 2 — 데이터 상세 흐름

```
[React Frontend]
       │
       │ FormData { sheet: File, audio: File, lang: "ko"|"en"|"ja"|"zh" }
       │
       ▼
[Go: handlers/analyze.go]
       │
       ├─ saveUploadedFile() → /tmp/xxx.xml, /tmp/xxx.wav
       │
       ▼
[Go: services/python_runner.go]
       │
       │ exec: python3 code/main.py --sheet <path> --audio <path> --json
       │
       ▼
[Python: code/main.py]
       │
       ├─ module1: extract_notes_from_musicxml(sheet)
       │     └─ { note, pitch, start, end, duration, velocity }[]
       │
       ├─ module2: extract_notes_from_audio(audio)
       │     └─ { note, pitch, start, end, duration, velocity }[]
       │
       └─ module3: compare_notes(expected, played)
             └─ {
                  score, correct, total,
                  missed_count, wrong_timing_count, extra_count,
                  avg_timing_deviation,
                  missed_notes[], wrong_timing_notes[], extra_notes[]
                }
       │
       │ stdout: JSON
       ▼
[Go: services/gpt.go + i18n.go]
       │
       ├─ BuildFeedbackPrompt(score, lang) → system + user prompt
       │
       └─ OpenAI API (gpt-4o-mini)
             └─ {
                  overall, pitch, rhythm, timing,
                  tips[], encouragement
                }
       │
       ▼
[Go: AnalyzeResponse JSON]
       │
       └─ { score: {...}, feedback: {...}, grade, lang }
       │
       ▼
[React: AnalysisPage.jsx]
       └─ 점수 바 + GPT 피드백 카드 렌더링
```

---

## 프로젝트 구조

```
capstone_music_ver2/
├── backend/                        # Go 백엔드 서버
│   ├── main.go                     # 서버 진입점 (포트 8080)
│   ├── go.mod                      # Go 모듈 정의
│   ├── handlers/
│   │   └── analyze.go              # POST /api/analyze 핸들러
│   ├── models/
│   │   └── types.go                # 공유 타입 (ScoreResult, FeedbackResult 등)
│   └── services/
│       ├── python_runner.go        # Python subprocess 실행
│       ├── gpt.go                  # OpenAI GPT API 호출
│       └── i18n.go                 # 언어별 프롬프트 생성
├── code/                           # Python 분석 파이프라인
│   ├── main.py                     # 파이프라인 진입점 (--json 플래그 지원)
│   ├── module1.py                  # MusicXML → 음표 추출
│   ├── module2.py                  # WAV → 음표 추출 (Piano Transcription)
│   └── module3.py                  # 음표 비교 및 채점
├── src/                            # React 프론트엔드
│   ├── App.jsx                     # 앱 루트, API 연동
│   ├── AnalysisPage.jsx            # 파일 업로드 + 피드백 UI
│   ├── HomePage.jsx                # 대시보드
│   ├── HistoryPage.jsx             # 연습 기록
│   ├── StatsPage.jsx               # 통계
│   └── ProfilePage.jsx             # 프로필
├── data/                           # 샘플 데이터
│   ├── piano_sheet_3.xml           # 샘플 악보
│   └── piano_record_3.wav          # 샘플 녹음
├── .env.example                    # 환경변수 템플릿
├── package.json                    # Node 의존성
└── requirements.txt                # Python 의존성
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| 프론트엔드 | React 19, Vite, 모바일 퍼스트 (max-width 480px) |
| 백엔드 | Go 1.24 (net/http) |
| 음악 분석 | Python, music21, librosa, piano_transcription_inference |
| AI 피드백 | OpenAI GPT-4o-mini |
| 지원 언어 | 한국어, English, 日本語, 中文 |

---

## 시작 가이드

### 사전 요구사항

- Go 1.21 이상
- Python 3.10 이상
- Node.js 18 이상
- OpenAI API Key

---

### 1단계 — 저장소 클론 및 브랜치 전환

```bash
git clone https://github.com/LEEjy0431/capstone_music_ver2.git
cd capstone_music_ver2
git checkout kts
```

---

### 2단계 — 환경변수 설정

```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env
```

`.env` 파일을 열어 값을 입력하세요:

```
OPENAI_API_KEY=sk-...        # OpenAI API 키
PORT=8080                    # Go 서버 포트 (기본값 8080)
VITE_API_BASE=http://localhost:8080   # React에서 바라볼 API 주소
```

---

### 3단계 — Python 의존성 설치

```bash
pip install -r requirements.txt
```

> Windows의 경우 가상환경 사용 권장:
> ```bash
> python -m venv capstone_env
> capstone_env\Scripts\activate
> pip install -r requirements.txt
> ```

---

### 4단계 — Go 백엔드 서버 실행

```bash
cd backend

# Windows
set OPENAI_API_KEY=sk-...
go run main.go

# macOS / Linux
OPENAI_API_KEY=sk-... go run main.go
```

서버가 정상 시작되면:
```
서버 시작: http://localhost:8080
```

헬스체크:
```bash
curl http://localhost:8080/health
# {"status":"ok"}
```

---

### 5단계 — React 프론트엔드 실행

새 터미널에서:

```bash
# 프로젝트 루트로 이동
cd capstone_music_ver2

npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

---

### 6단계 — 사용 방법

1. 브라우저에서 앱 실행 후 **분석** 탭으로 이동
2. **연주 음원 파일 (WAV)** 업로드
3. **악보 파일 (MusicXML)** 업로드
4. **피드백 언어** 선택 (한국어 / English / 日本語 / 中文)
5. **분석 시작하기** 버튼 클릭
6. 결과 확인:
   - 점수 및 등급 (A ~ C)
   - 정확한 음표 / 놓친 음표 / 박자 오류 수
   - GPT 생성 피드백 (종합 평가 / 음정 / 리듬 / 타이밍 / 개선 팁 / 격려)

---

### Python 파이프라인 단독 실행 (테스트용)

```bash
cd capstone_music_ver2

# 기존 콘솔 출력 모드
python code/main.py --sheet data/piano_sheet_3.xml --audio data/piano_record_3.wav

# JSON 모드 (Go 연동과 동일한 출력)
python code/main.py --sheet data/piano_sheet_3.xml --audio data/piano_record_3.wav --json
```

---

## API 명세

### `POST /api/analyze`

**Request** — `multipart/form-data`

| 필드 | 타입 | 설명 |
|------|------|------|
| `sheet` | File | 악보 파일 (MusicXML, .xml) |
| `audio` | File | 연주 음원 파일 (.wav) |
| `lang` | string | 피드백 언어 코드 (`ko` / `en` / `ja` / `zh`), 기본값 `ko` |

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
    "avg_timing_deviation": 0.087,
    "missed_notes": [...],
    "wrong_timing_notes": [...],
    "extra_notes": [...]
  },
  "feedback": {
    "overall": "전반적으로 안정적인 연주입니다...",
    "pitch": "음정 정확도는 83.5%로 양호합니다...",
    "rhythm": "박자 오류가 5회 발생했습니다...",
    "timing": "평균 타이밍 편차 0.087초는 수용 가능한 수준입니다...",
    "tips": ["메트로놈과 함께 연습하세요", "..."],
    "encouragement": "꾸준한 노력이 보이는 연주입니다!"
  },
  "grade": "B+",
  "lang": "ko"
}
```

**등급 기준**

| 점수 | 등급 |
|------|------|
| 90점 이상 | A |
| 85점 이상 | A- |
| 80점 이상 | B+ |
| 75점 이상 | B |
| 70점 이상 | C+ |
| 70점 미만 | C |

### `GET /health`

서버 상태 확인

```json
{"status": "ok"}
```

---

## 트러블슈팅

**Go 서버 실행 시 `OPENAI_API_KEY 환경변수가 설정되지 않았습니다` 오류**
→ `.env` 파일의 키를 환경변수로 직접 export하거나 서버 실행 시 앞에 붙여서 실행하세요.

**Python 실행 실패 오류**
→ `pip install -r requirements.txt`가 완료되었는지 확인하고, 가상환경이 활성화된 상태에서 Go 서버를 실행하세요.

**CORS 오류 (브라우저)**
→ Go 서버가 `http://localhost:8080`에서 실행 중인지 확인하고, `.env`의 `VITE_API_BASE` 값과 일치하는지 확인하세요.

**WAV 파일 업로드 후 분석 실패**
→ 파일이 표준 WAV 포맷(PCM, 모노 또는 스테레오)인지 확인하세요. MP3는 WAV로 변환 후 사용하세요.
