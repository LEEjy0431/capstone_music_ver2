# Master Prompt — 멀티스택 AI 파이프라인 프로젝트 프레임

> 이 프롬프트를 Claude Code(또는 동급 AI 에이전트)에게 전달하면,  
> 아래에 정의된 구조·문서화·코드 규칙·라이브러리 관리 방식이 동일하게 재현됩니다.  
> 프로젝트명, 기술 스택, 도메인은 `[ ]` 안의 값을 교체하여 사용하세요.

---

## 0. 이 프롬프트의 사용법

```
아래 Master Prompt 전체를 대화의 첫 메시지로 붙여넣고,
마지막 줄에 실제 작업 지시를 추가한다.

예:
  [Master Prompt 전체]
  ---
  지시: Python 분석 파이프라인 module1.py를 작성해줘.
```

---

## 1. 프로젝트 컨텍스트

```
프로젝트명  : [PROJECT_NAME]
저장소      : https://github.com/[ORG]/[REPO]
개발 브랜치 : [BRANCH]  (main 브랜치 직접 push 금지)
팀 환경     : macOS (Apple Silicon M1/M2/M3) + Windows 혼용
주요 언어   : Python · Go · Flutter(Dart) · React(JSX)
AI 모델     : OpenAI GPT-4o-mini  (또는 [LLM_MODEL])
```

---

## 2. 필수 폴더 구조

에이전트는 아래 구조를 기준으로 파일을 생성·수정한다.  
새 폴더가 추가될 때마다 해당 폴더에 `README.md`를 함께 생성한다.

```
[PROJECT_ROOT]/
├── [pipeline_folder]/          # Python AI/분석 파이프라인  ← Anaconda 관리
│   ├── main.py                 # CLI 진입점
│   ├── module1.py … moduleN.py # 단계별 처리 모듈
│   ├── environment.yml         # Anaconda 환경 정의
│   └── README.md
├── [backend_folder]/           # Go HTTP 서버
│   ├── main.go
│   ├── go.mod
│   ├── handlers/
│   ├── models/
│   ├── services/
│   └── README.md
├── [frontend_folder]/          # Flutter 앱 (Web + Android)
│   ├── pubspec.yaml
│   ├── lib/
│   │   ├── main.dart
│   │   ├── models/
│   │   ├── services/
│   │   ├── providers/
│   │   ├── pages/
│   │   └── widgets/
│   ├── android/app/src/main/AndroidManifest.xml
│   ├── web/index.html
│   └── README.md
├── data/                       # 샘플 데이터 (수정 금지)
├── docs/                       # 모든 문서 (아래 §3 참조)
├── .env.example
├── requirements.txt            # Python 분석 스택
├── requirements-llm.txt        # Python LLM 스택
├── requirements-mac.txt        # macOS 전용 오버라이드
└── README.md                   # 루트 — Level 0/1/2 DFD 포함
```

---

## 3. `docs/` 폴더 — 필수 문서 목록

에이전트는 작업 시작 전 아래 파일들이 존재하는지 확인하고, 없으면 생성한다.

| 파일 | 역할 | 업데이트 시점 |
|------|------|--------------|
| `docs/TODO.md` | 우선순위별 미완료 작업 목록 | 작업 완료 시 ✅ 표시 |
| `docs/PROGRESS.md` | 스프린트별 누적 개발 기록 | 스프린트 완료 시 섹션 추가 |
| `docs/AGENT_GUIDELINES.md` | AI 에이전트 수정 규칙 | 규칙 변경 시 |
| `docs/GUIDE_MAC.md` | macOS 팀원 환경 설정 가이드 | 스택 변경 시 |
| `docs/RESEARCH_[TOPIC].md` | 기술 선택·연구 분석 문서 | 연구 완료 시 |

### `docs/TODO.md` 형식

```markdown
## [영역명]

| 상태 | 항목 | 담당 | 비고 |
|------|------|------|------|
| 🔴  | 항목 | —   | 필수 (블로킹) |
| 🟡  | 항목 | —   | 중요 (다음 스프린트) |
| 🟢  | 항목 | —   | 개선 (여유 시) |
| ✅  | 항목 | —   | 완료 |
```

### `docs/PROGRESS.md` 형식

```markdown
## [Sprint N] YYYY-MM-DD — 스프린트 제목

### 완료 항목
- 파일명: 변경 내용 한 줄

### 주요 결정 사항
- 기술 선택 이유, 트레이드오프

### 발생한 문제 & 해결
- 문제 → 원인 → 해결책

### 다음 스프린트 예정
- ...
```

---

## 4. README 작성 규칙

모든 `README.md`는 아래 4개 섹션을 반드시 포함한다.

### 4-1. 폴더 구조 (트리 형식)
### 4-2. DFD (Data Flow Diagram) — 3단계

```
Level 0 : 컨텍스트 다이어그램 (입력 → 시스템 → 출력)
Level 1 : 주요 프로세스 흐름 (박스·화살표 ASCII)
Level 2 : 데이터 타입·필드 상세 흐름
```

ASCII DFD 예시:
```
[입력] ──► [처리 A] ──► [처리 B] ──► [출력]
               │                │
               ▼                ▼
          [저장소 X]        [외부 API]
```

### 4-3. 라이브러리 설치 매뉴얼

각 스택별로 아래 항목을 포함한다:

- **런타임 설치** (Python/Go/Flutter/Node 버전 확인 명령 포함)
- **의존성 설치 명령** (OS별 분기: macOS / Linux / Windows)
- **설치 확인 명령**
- **라이브러리 목록 표** (패키지명 | 버전 | 역할)
- **캐시·오류 초기화** 명령

### 4-4. 트러블슈팅 표

```markdown
| 증상 | 원인 | 해결 |
|------|------|------|
| ... | ... | ... |
```

---

## 5. 코드 컨벤션 — 스택별

### 5-1. Python (`[pipeline_folder]/`)

**stdout / stderr 분리 규칙** (가장 중요):
```python
import sys, json

# ✅ 진단 메시지 → stderr (Go subprocess JSON 파싱 보호)
print(f"[진단] 값: {value}", file=sys.stderr)

# ✅ 결과 데이터 → stdout (순수 JSON만)
print(json.dumps(result, ensure_ascii=False))
```

```python
# ❌ 금지 — stdout 오염으로 Go JSON 파싱 실패
print(f"값: {value}")
```

**CLI 인터페이스** (`main.py`):
```python
parser.add_argument("--json",     dest="json_mode",     action="store_true")
parser.add_argument("--feedback", dest="feedback_mode", action="store_true")
# --json 모드: stdout = 순수 JSON
# --feedback 모드: stdout = {score, feedback, lang} JSON
```

**모듈 명명**: `module1.py` → `module2.py` → … `moduleN.py` 순번 체계  
**환경변수**: `os.environ.get("KEY")` 사용, 하드코딩 금지  
**에러 출력**: `print(json.dumps({"error": str(e)}))` → `sys.exit(1)`

### 5-2. Go (`[backend_folder]/`)

**CORS — 반드시 최상위 미들웨어로**:
```go
// main.go
func corsHandler(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Access-Control-Allow-Origin", "*")
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept")
        if r.Method == http.MethodOptions {
            w.WriteHeader(http.StatusNoContent)
            return
        }
        next.ServeHTTP(w, r)
    })
}
// log.Fatal(http.ListenAndServe(addr, corsHandler(mux)))
```

**Python 경로 탐색** (하드코딩 금지):
```go
func projectRoot() (string, error) {
    if root := os.Getenv("PROJECT_ROOT"); root != "" {
        return filepath.Abs(root)
    }
    exe, _ := os.Executable()
    return filepath.Abs(filepath.Dir(filepath.Dir(exe)))
}
```

**SSE 스트리밍 패턴**:
```go
w.Header().Set("Content-Type", "text/event-stream")
w.Header().Set("Cache-Control", "no-cache")
w.Header().Set("X-Accel-Buffering", "no")
flusher := w.(http.Flusher)
fmt.Fprintf(w, "event: chunk\ndata: %s\n\n", data)
flusher.Flush()
```

**JSON 응답 헬퍼**:
```go
func writeJSON(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(v)
}
```

### 5-3. Flutter / Dart (`[frontend_folder]/`)

**API 서비스 분리** — 페이지에서 직접 호출 금지:
```dart
// lib/services/api_service.dart 에서만 HTTP 호출
static String get baseUrl {
    const env = String.fromEnvironment('API_BASE', defaultValue: 'http://localhost:8080');
    return env;
}
```

**파일 바이트 통일** (Web·Android 공통):
```dart
// withData: true 필수 — PlatformFile.path 에 의존하지 않음
final res = await FilePicker.platform.pickFiles(withData: true, ...);
final bytes = res.files.first.bytes!;
```

**상태 관리** — ChangeNotifier Provider 패턴:
```
lib/providers/[domain]_provider.dart  ← ChangeNotifier
lib/pages/[name]_page.dart            ← context.watch<Provider>()
lib/services/api_service.dart         ← HTTP 호출
```

**SSE 스트림 수신**:
```dart
await for (final chunk in response.stream.transform(utf8.decoder)) {
    final blocks = raw.split('\n\n');
    // "data: {...}" 파싱 → yield FeedbackEvent
}
```

### 5-4. React / JavaScript (`src/`)

**API Base URL**:
```javascript
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080';
```

**레거시 유지 원칙**: 새 기능 추가 금지, 버그 수정만 허용

---

## 6. LLM 피드백 출력 패턴

### 6-1. 구조화 출력 (JSON Schema Strict)

```go
// services/i18n_schema.go
var feedbackJSONSchema = map[string]any{
    "type": "json_schema",
    "json_schema": map[string]any{
        "name":   "[domain]_feedback",
        "strict": true,
        "schema": map[string]any{
            "type":                 "object",
            "properties":          { /* 필드 정의 */ },
            "required":            []string{ /* 필수 필드 */ },
            "additionalProperties": false,
        },
    },
}
```

```go
// gpt.go — 최적화 파라미터
Temperature: 0.3,    // JSON 안정성 우선
MaxTokens:   400,    // 응답 길이 제한
// system prompt: ~90 토큰 (역할+언어+지시만)
// user prompt:   ~60 토큰 (수치 데이터만)
```

### 6-2. SSE 스트리밍 흐름

```
클라이언트 요청 (GET /api/[stream_endpoint])
    │
    ▼
Go: stream: true → OpenAI API
    │
    ├── bufio.Scanner → "data: {delta}" 파싱
    ├── event: chunk  → 클라이언트로 즉시 전달 (Flush)
    └── event: done   → 완성 JSON 파싱 후 전달
    │
    ▼
Flutter: SSE 수신 → 텍스트 누적 표시 → done 시 구조화 카드로 전환
```

**엔드포인트 명명**: `GET /api/[resource]/stream`  
**이벤트 타입**: `chunk` | `done` | `error`  
**Heartbeat**: 15초마다 `: heartbeat\n\n` 전송 (연결 유지)

---

## 7. 라이브러리 관리 — 스택별 규칙

### Python — Anaconda (`environment.yml`)

```yaml
name: [env_name]
channels:
  - conda-forge
  - pytorch
  - defaults
dependencies:
  - python=[버전]
  - [conda 설치 가능한 패키지]
  - pip:
    - [conda 불가 패키지=고정버전]
    # macOS: [패키지-macos=버전]  (주석으로 병기)
    # Linux: [패키지=버전]
```

- conda 채널 우선순위: `conda-forge` → `pytorch` → `defaults`
- 버전은 `==` 고정, macOS 전용 패키지는 주석으로 병기
- 분석 스택(`requirements.txt`) / LLM 스택(`requirements-llm.txt`) / macOS 전용(`requirements-mac.txt`) 분리

```bash
# macOS Apple Silicon 환경 생성
CONDA_SUBDIR=osx-arm64 conda env create -f [pipeline_folder]/environment.yml
conda activate [env_name]
pip uninstall tensorflow -y
pip install tensorflow-macos==[버전]
```

### Go — 표준 라이브러리 우선

```bash
cd [backend_folder]
go mod download   # 의존성 다운로드
go mod tidy       # 미사용 제거
go build ./...    # 빌드 검증
```

- 외부 패키지 추가 전 표준 라이브러리(`net/http`, `encoding/json` 등)로 구현 가능한지 먼저 검토
- OpenAI API는 `net/http`로 직접 호출 (SDK 불필요)

### Flutter — pub.dev

```bash
cd [frontend_folder]
flutter pub get               # 설치
flutter pub upgrade           # 업그레이드
flutter pub cache clean       # 캐시 초기화
flutter pub deps              # 설치 목록 확인
```

- `pubspec.yaml` 변경 시 반드시 `flutter pub get` 재실행
- `^` 버전 범위 사용 권장

### React — npm

```bash
npm install                          # 설치
npm list --depth=0                   # 목록 확인
rm -rf node_modules && npm install   # 재설치
```

---

## 8. 환경변수 관리

### `.env.example` 필수 항목

```env
# LLM API
OPENAI_API_KEY=sk-...

# Go 서버
PORT=8080
PROJECT_ROOT=[프로젝트 절대 경로]

# React
VITE_API_BASE=http://localhost:8080
```

### Flutter — dart-define 주입

```bash
flutter run -d chrome --dart-define=API_BASE=http://localhost:8080
flutter build apk --dart-define=API_BASE=http://[서버IP]:8080
```

### 규칙

- `.env` 파일은 `.gitignore`에 포함 — 절대 커밋하지 않음
- 시크릿 하드코딩 금지 (API 키, 토큰 등)
- 새 환경변수 추가 시 `.env.example` + 해당 폴더 README 동시 업데이트

---

## 9. Git 워크플로우

### 브랜치 구조

```
main          ← 배포 브랜치 (직접 push 금지)
[dev_branch]  ← 통합 개발 브랜치 (기본 작업 브랜치)
feature/*     ← 기능 개발 (dev_branch에서 분기)
claude/*      ← AI 에이전트 작업 브랜치
```

### 커밋 메시지

```
<type>(<scope>): <요약>

<선택적 본문 — 무엇을, 왜>
```

| type | 사용 상황 |
|------|-----------|
| `feat` | 새 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서만 변경 |
| `chore` | 빌드·의존성·설정 변경 |
| `refactor` | 기능 변화 없는 구조 개선 |

### Push 명령 (토큰 인증)

```bash
git push https://[USERNAME]:[TOKEN]@github.com/[ORG]/[REPO].git [BRANCH]
```

### 작업 완료 체크리스트

```
□ go build ./...  또는  flutter pub get  으로 빌드 오류 없음 확인
□ docs/TODO.md 완료 항목 ✅ 표시
□ docs/PROGRESS.md 스프린트 섹션 업데이트
□ 변경된 폴더의 README.md 업데이트
□ git add → commit → push
```

---

## 10. 에이전트 행동 규칙

### 항상 할 것

1. **파일 수정 전 반드시 Read** — 기존 내용 파악 후 Edit
2. **빌드 검증 후 커밋** — `go build ./...` / `flutter pub get` / `python -c "import ..."` 
3. **문서 동기화** — 코드 변경 시 해당 README도 함께 수정
4. **병렬 처리** — 독립적인 파일 작업은 동시에 수행

### 절대 하지 말 것

| 금지 행동 | 이유 |
|-----------|------|
| Python 모듈에서 `print()` (stderr 없이) | Go subprocess JSON 파싱 오류 |
| Go 핸들러 내부에 CORS 헤더 추가 | `main.go` corsHandler와 중복 |
| API URL·시크릿 하드코딩 | 환경 분리 불가, 보안 위험 |
| `data/` 파일 삭제·교체 | 파이프라인 기본 테스트 파일 |
| `.env` 커밋 | API 키 노출 |
| `main` 브랜치 직접 push | 배포 브랜치 보호 |
| LLM 응답 파싱 없이 그대로 사용 | JSON 파싱 실패 방어 없음 |

### 연구·탐색 요청 시

1. `docs/RESEARCH_[TOPIC].md` 생성
2. 현재 구조의 문제 분석 → 개선 방향 3가지 비교 → 권장 조합 선택
3. 프로토타입 구현 후 빌드 검증
4. `docs/PROGRESS.md` 에 연구 결과 기록

---

## 11. macOS (Apple Silicon) 크로스플랫폼 규칙

| 항목 | macOS 처리 | Linux/Windows 처리 |
|------|-----------|-------------------|
| TensorFlow | `tensorflow-macos` + `tensorflow-metal` | `tensorflow` |
| conda 환경 생성 | `CONDA_SUBDIR=osx-arm64 conda env create` | `conda env create` |
| onnxruntime | `onnxruntime-silicon` (오류 시) | `onnxruntime` |
| Flutter Android 빌드 | Android Studio 별도 설치 | SDK 경로 설정 |
| API 주소 (Android) | `ipconfig getifaddr en0` 로 PC IP 확인 | `hostname -I` |

- macOS 전용 패키지는 `requirements-mac.txt` 또는 `environment.yml` 주석으로 병기
- `docs/GUIDE_MAC.md` 에 전체 Mac 설치 절차 유지

---

## 12. 응용 — 이 프레임으로 새 프로젝트 시작하기

아래 순서로 진행하면 동일한 구조가 재현됩니다.

```
Step 1. 저장소 초기화
  └─ 폴더 구조 생성 + .gitignore + .env.example

Step 2. 각 폴더 스캐폴딩
  └─ pipeline/: main.py + moduleN.py + environment.yml + README.md
  └─ backend/:  main.go + go.mod + handlers/ + services/ + README.md
  └─ frontend/: pubspec.yaml + lib/ + AndroidManifest.xml + README.md

Step 3. docs/ 초기화
  └─ TODO.md + PROGRESS.md + AGENT_GUIDELINES.md + GUIDE_MAC.md

Step 4. 루트 README.md 작성
  └─ Level 0/1/2 DFD + 기술 스택 표 + 실행 가이드 + API 명세

Step 5. 각 폴더 README.md 작성
  └─ 폴더 구조 + DFD + 라이브러리 설치 매뉴얼 + 트러블슈팅

Step 6. 핵심 기능 구현 (스택 순서)
  └─ Python 파이프라인 → Go 백엔드 → Flutter 프론트엔드

Step 7. LLM 연동
  └─ 구조화 출력(JSON Schema Strict) + SSE 스트리밍 엔드포인트

Step 8. 커밋·푸시 + docs/PROGRESS.md 기록
```
