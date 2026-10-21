# code/ — Python 분석 파이프라인

피아노 악보(MusicXML)와 연주 음원(WAV)을 분석하여 음표를 추출·비교·채점하고, GPT 기반 피드백을 생성하는 Python 파이프라인입니다.

---

## 폴더 구조

```
code/
├── main.py       # 파이프라인 진입점 (CLI + Go subprocess 연동)
├── module1.py    # MusicXML → 음표 추출
├── module2.py    # WAV → 음표 추출 (Piano Transcription)
├── module3.py    # 음표 비교 및 채점
└── module4.py    # GPT 기반 피드백 생성 (OpenAI)
```

---

## DFD (Data Flow Diagram)

### Level 1 — 전체 파이프라인

```
     악보 파일          연주 음원 파일
   (MusicXML .xml)      (WAV .wav)
         │                   │
         ▼                   ▼
  ┌─────────────┐    ┌─────────────────┐
  │  module1.py │    │   module2.py    │
  │  MusicXML   │    │  Piano 전사     │
  │  파싱       │    │  모델 (WAV→MIDI)│
  └──────┬──────┘    └───────┬─────────┘
         │                   │
         │ expected_notes[]  │ played_notes[]
         │  { note, pitch,   │  { note, pitch,
         │    start, end,    │    start, end,
         │    duration,      │    duration,
         │    velocity }     │    velocity }
         │                   │
         └─────────┬─────────┘
                   │
                   ▼
          ┌─────────────────┐
          │   module3.py    │
          │  음표 비교·채점  │
          └────────┬────────┘
                   │
                   │ ScoreResult {
                   │   score, correct, total,
                   │   missed_count,
                   │   wrong_timing_count,
                   │   extra_count,
                   │   avg_timing_deviation,
                   │   missed_notes[],
                   │   wrong_timing_notes[],
                   │   extra_notes[]
                   │ }
                   │
          ┌────────▼────────┐
          │   module4.py    │  ← OPENAI_API_KEY
          │  GPT 피드백     │
          │  생성 (선택)    │
          └────────┬────────┘
                   │
                   │ FeedbackResult {
                   │   overall, pitch, rhythm,
                   │   timing, tips[],
                   │   encouragement
                   │ }
                   ▼
               최종 결과
```

### Level 2 — 각 모듈 내부 흐름

```
┌──────────────────────────────────────────────────────────────┐
│  module1.py — MusicXML 파싱                                  │
│                                                              │
│  converter.parse(xml_path)                                   │
│       │                                                      │
│       ├─ MetronomeMark 탐색 → BPM 추출                       │
│       │   └─ 없으면 XML <sound tempo> 태그 폴백              │
│       │                                                      │
│       ├─ score.parts 순회                                    │
│       │   ├─ note.Note  → { note, pitch, start, end, ... }   │
│       │   └─ chord.Chord → 각 음표로 분해                    │
│       │                                                      │
│       └─ 시작시간·피치 정렬 → expected_notes[]               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  module2.py — 오디오 전사                                    │
│                                                              │
│  soundfile.read(wav) → mono 변환                             │
│       │                                                      │
│       ├─ librosa.resample() → 16kHz                          │
│       │                                                      │
│       ├─ PianoTranscription(device='cpu')                    │
│       │   └─ transcribe(audio) → tmp.mid                     │
│       │                                                      │
│       ├─ pretty_midi.PrettyMIDI(tmp.mid)                     │
│       │   └─ 모든 instrument notes 수집                      │
│       │                                                      │
│       ├─ quantize_time(t, grid)  ← BPM 기반 16분음표 grid    │
│       │                                                      │
│       └─ 정렬 → played_notes[]                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  module3.py — 채점                                           │
│                                                              │
│  group_chords(notes, chord_tolerance=0.05s)                  │
│       │                                                      │
│       ├─ expected_groups[] ← 정답 화음 그룹                  │
│       └─ played_groups[]   ← 연주 화음 그룹                  │
│                                                              │
│  매칭 (time_tolerance=0.2s)                                  │
│       ├─ 최근접 연주 그룹 탐색                               │
│       ├─ 피치 집합 교집합 → correct++                        │
│       ├─ 타이밍 초과 → wrong_timing                          │
│       └─ 대응 없음 → missed                                  │
│                                                              │
│  score = correct / total * 100                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  module4.py — GPT 피드백                                     │
│                                                              │
│  _build_prompt(score, lang)                                  │
│       └─ system prompt (언어 지시 + JSON 구조)               │
│       └─ user prompt   (채점 결과 수치)                      │
│                                                              │
│  OpenAI().chat.completions.create(                           │
│    model="gpt-4o-mini",                                      │
│    response_format={"type":"json_object"},                   │
│    messages=[system, user]                                   │
│  )                                                           │
│       └─ content → json.loads() → FeedbackResult            │
└──────────────────────────────────────────────────────────────┘
```

---

## 라이브러리 설치

### 방법 1 — pip (Windows / Linux)

```bash
# 프로젝트 루트에서 실행
# 분석 스택 + LLM 스택 전체 설치
pip install -r requirements.txt -r requirements-llm.txt
```

### 방법 2 — pip (macOS Apple Silicon)

```bash
# tensorflow-macos 포함 전체 설치
pip install -r requirements.txt -r requirements-mac.txt -r requirements-llm.txt

# tensorflow-macos 설치 실패 시 수동 설치
pip uninstall tensorflow -y
pip install tensorflow-macos==2.16.2
pip install tensorflow-metal   # GPU 가속 (선택)
```

### 방법 3 — Anaconda (권장, macOS / Linux)

```bash
# 최초 1회: 환경 생성
CONDA_SUBDIR=osx-arm64 conda env create -f code/environment.yml   # Apple Silicon
conda env create -f code/environment.yml                           # Intel / Linux

# 환경 활성화
conda activate capstone_music

# macOS: tensorflow 수동 교체 (필수)
pip uninstall tensorflow -y
pip install tensorflow-macos==2.16.2

# 환경 업데이트 (environment.yml 변경 시)
conda env update -f code/environment.yml --prune
```

### 설치 확인

```bash
conda activate capstone_music   # 또는 pip 가상환경 활성화

python -c "
import torch, music21, librosa, pretty_midi
import piano_transcription_inference
import openai
print('모든 라이브러리 정상')
print('PyTorch:', torch.__version__)
print('music21:', music21.VERSION_STR)
"
```

### 라이브러리 목록

#### 분석 스택 (`requirements.txt`)

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| `librosa` | 0.11.0 | 오디오 파일 로딩, 리샘플링 |
| `soundfile` | 0.13.1 | WAV 파일 읽기/쓰기 |
| `resampy` | 0.4.3 | 고품질 오디오 리샘플링 |
| `soxr` | 1.0.0 | 빠른 샘플레이트 변환 |
| `audioread` | 3.1.0 | 다양한 오디오 포맷 디코딩 |
| `music21` | 9.9.1 | MusicXML 파싱, 악보 분석 |
| `pretty_midi` | 0.2.11 | MIDI 파일 파싱·생성 |
| `mido` | 1.3.3 | 저수준 MIDI I/O |
| `piano-transcription-inference` | 0.0.6 | WAV→MIDI 피아노 전사 모델 |
| `torch` | 2.1.0 | PyTorch 딥러닝 프레임워크 |
| `torchlibrosa` | 0.1.0 | PyTorch 기반 오디오 특성 추출 |
| `onnxruntime` | 1.24.4 | ONNX 모델 추론 |
| `tensorflow` | 2.16.2 | 딥러닝 (Linux/Windows) |
| `tensorflow-macos` | 2.16.2 | 딥러닝 (macOS 전용) |
| `numpy` | 1.26.4 | 수치 배열 연산 |
| `scipy` | 1.11.4 | 신호 처리, 과학 연산 |
| `scikit-learn` | 1.8.0 | 머신러닝 유틸리티 |
| `numba` | 0.65.0 | JIT 컴파일 (librosa 가속) |

#### LLM 스택 (`requirements-llm.txt`)

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| `openai` | ≥1.30.0 | GPT-4o-mini API 호출 (module4) |
| `python-dotenv` | ≥1.0.0 | `.env` 파일 환경변수 로딩 |

#### macOS 전용 (`requirements-mac.txt`)

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| `tensorflow-macos` | 2.16.2 | Apple Silicon 네이티브 TensorFlow |
| `tensorflow-metal` | — | GPU 가속 플러그인 (선택) |

---

## 실행 방법

### 콘솔 모드 (개발·테스트)

```bash
cd capstone_music_ver2

python code/main.py \
  --sheet data/piano_sheet_3.xml \
  --audio data/piano_record_3.wav
```

출력 예시:
```
=== 피아노 연주 자동 평가 시스템 ===

1. 정답 악보(MIDI) 분석 중...
-> 총 80개의 정답 음표 추출 완료

2. 사용자 연주(WAV) 분석 중...
-> 총 76개의 실제 연주 음표 추출 완료

3. 채점 중...
===== 채점 결과 =====
점수:              83.5점 / 100점
정확한 음표:       67 / 80개
누락된 음표:       8개
박자 오류:         5개
```

---

### JSON 모드 (Go 서버 연동)

```bash
python code/main.py \
  --sheet data/piano_sheet_3.xml \
  --audio data/piano_record_3.wav \
  --json
```

출력 (stdout — 순수 JSON):
```json
{
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
}
```

> stdout에는 JSON만 출력됩니다. BPM 감지 등 진단 메시지는 stderr로 출력됩니다.

---

### 피드백 모드 (채점 + GPT 피드백 통합)

```bash
export OPENAI_API_KEY=sk-...

python code/main.py \
  --sheet data/piano_sheet_3.xml \
  --audio data/piano_record_3.wav \
  --feedback \
  --lang ko
```

출력:
```json
{
  "score": { ... },
  "feedback": {
    "overall": "전반적으로 안정적인 연주입니다...",
    "pitch": "음정 정확도 83.5%...",
    "rhythm": "박자 오류 5회...",
    "timing": "평균 편차 0.087초...",
    "tips": ["메트로놈 연습", "..."],
    "encouragement": "화이팅!"
  },
  "lang": "ko"
}
```

---

### module4 단독 테스트

```bash
export OPENAI_API_KEY=sk-...

# 한국어 피드백
python code/module4.py ko

# 영어 피드백
python code/module4.py en
```

---

## CLI 옵션 전체 목록

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--sheet` | `data/piano_sheet_3.xml` | 악보 파일 경로 (MusicXML) |
| `--audio` | `data/piano_record_3.wav` | 연주 음원 경로 (WAV) |
| `--lang` | `ko` | 피드백 언어 (`ko` / `en` / `ja` / `zh`) |
| `--json` | — | 채점 결과만 JSON 출력 (Go 연동용) |
| `--feedback` | — | 채점 + GPT 피드백 JSON 출력 |

---

## 채점 기준

| 항목 | 설명 | 파라미터 |
|------|------|----------|
| **time_tolerance** | 타이밍 오차 허용 범위 | `0.2초` |
| **chord_tolerance** | 화음 묶음 기준 범위 | `0.05초` |
| **score** | 정확한 음표 / 전체 음표 × 100 | — |

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `ModuleNotFoundError: piano_transcription_inference` | 의존성 미설치 | `pip install -r requirements.txt` |
| `ModuleNotFoundError: openai` | LLM 의존성 미설치 | `pip install -r requirements-llm.txt` |
| `OPENAI_API_KEY 환경변수가 설정되지 않았습니다` | 환경변수 누락 | `export OPENAI_API_KEY=sk-...` |
| module1 BPM이 120으로 고정 | XML에 tempo 태그 없음 | 악보 파일 BPM 정보 확인 |
| module2 음표 추출 실패 | WAV 포맷 문제 | PCM WAV로 변환 후 재시도 |
