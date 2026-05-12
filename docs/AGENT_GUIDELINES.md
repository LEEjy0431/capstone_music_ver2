# Agent Guideline

> AI 에이전트(Claude Code 등)가 이 저장소를 수정할 때 반드시 따라야 할 규칙과 컨텍스트.  
> 팀 개발 환경: macOS (Apple Silicon) + Anaconda, Go, Flutter

---

## 1. 저장소 구조와 책임 경계

```
capstone_music_ver2/
├── code/          ← Python 파이프라인  [관리: main 브랜치 관리자 / Anaconda]
├── backend/       ← Go HTTP 서버       [팀 공동]
├── flutter_app/   ← Flutter (Web+Android) [팀 공동]
├── src/           ← React (레거시, 유지만)  [수정 최소화]
├── data/          ← 샘플 데이터         [수정 금지]
└── docs/          ← 이 폴더             [모든 문서 여기에]
```

### 영역별 수정 규칙

| 폴더 | 수정 권한 | 주의 사항 |
|------|-----------|-----------|
| `code/` | main 브랜치 관리자 우선 | `environment.yml` 변경 시 반드시 팀 공유 |
| `code/environment.yml` | main 브랜치 관리자 | 변경 후 `docs/PROGRESS.md` 에 기록 |
| `backend/` | 팀 공동 | Go 모듈(`go.mod`) 변경 시 사유 명시 |
| `flutter_app/` | 팀 공동 | `pubspec.yaml` 변경 시 `flutter pub get` 필요 안내 |
| `src/` | 최소 수정 | 새 기능 추가 금지, 버그 수정만 허용 |
| `data/` | 수정 금지 | 샘플 파일 교체 시 팀 합의 필요 |
| `docs/` | 모든 구성원 | 작업 완료 후 반드시 `PROGRESS.md` 업데이트 |

---

## 2. 개발 환경 전제 조건

에이전트가 코드를 수정하기 전에 아래 환경을 가정합니다.

### Python (`code/`)
- **관리 도구**: Anaconda (`conda`)
- **환경 파일**: `code/environment.yml`
- **환경 이름**: `capstone_music`
- **Python 버전**: 3.10
- **macOS Apple Silicon 주의**: `tensorflow-macos==2.16.2` 사용, `tensorflow` 제거 필요

```bash
# 환경 확인 명령
conda env list | grep capstone_music
conda activate capstone_music
python -c "import torch, music21, librosa; print('OK')"
```

### Go (`backend/`)
- **버전**: 1.21 이상
- **모듈 경로**: `capstone/backend`
- **필수 환경변수**: `OPENAI_API_KEY`, `PROJECT_ROOT`

### Flutter (`flutter_app/`)
- **SDK 버전**: 3.10 이상
- **API 주소 주입**: `--dart-define=API_BASE=http://localhost:8080`
- **지원 타깃**: Web (Chrome), Android (API 24+)

---

## 3. `code/` 수정 지침 (Anaconda 관리 영역)

> `code/` 폴더는 main 브랜치 관리자가 Anaconda 환경으로 관리합니다.  
> 에이전트가 이 영역을 수정할 때는 아래 규칙을 따르세요.

### 3-1. 패키지 추가 / 제거

1. `code/environment.yml` 을 수정합니다.
2. conda 채널 우선순위: `conda-forge` → `pytorch` → `defaults`
3. conda로 설치할 수 없는 패키지만 `pip:` 섹션에 추가합니다.
4. 버전은 **고정 버전** (`==`) 사용을 원칙으로 합니다.
5. macOS 전용 패키지는 주석으로 병기합니다.

```yaml
# 올바른 예
  - pip:
    - some-package==1.2.3       # Linux/Windows
    # - some-package-mac==1.2.3 # macOS 전용 (수동 교체)
```

6. 변경 후 `docs/PROGRESS.md` 에 변경 사유를 기록합니다.

### 3-2. Python 파일 수정 규칙

- `module1.py` / `module2.py`: **모든 print를 `sys.stderr`로 출력**합니다.
  - stdout은 Go subprocess가 JSON 파싱에 사용하므로 오염 금지.
- `module4.py`: `OPENAI_API_KEY` 환경변수를 직접 읽습니다. 하드코딩 금지.
- `main.py`: `--json` 모드 stdout은 **순수 JSON만** 출력해야 합니다.

```python
# 올바른 예
import sys
print(f"[진단] BPM: {bpm}", file=sys.stderr)   # ✅ 진단 메시지
print(json.dumps(result))                        # ✅ JSON 출력
```

```python
# 잘못된 예
print(f"BPM: {bpm}")                            # ❌ stdout 오염
```

### 3-3. 새 모듈 추가 시

1. `code/module{N}.py` 로 명명합니다.
2. `code/main.py` 의 임포트 및 파이프라인에 연결합니다.
3. `code/README.md` 의 폴더 구조와 DFD를 업데이트합니다.
4. 의존 패키지는 `code/environment.yml` 에 추가합니다.

---

## 4. `backend/` 수정 지침

### CORS
- CORS 설정은 `backend/main.go` 의 `corsHandler` 에서만 관리합니다.
- 핸들러 내부에 CORS 헤더를 추가하지 않습니다.

### Python 경로
- `backend/services/python_runner.go` 의 `projectRoot()` 함수를 통해 경로를 해결합니다.
- `code/main.py` 의 경로를 하드코딩하지 않습니다.

### 환경변수
- 새 환경변수 추가 시 `.env.example` 과 `backend/README.md` 를 함께 업데이트합니다.

---

## 5. `flutter_app/` 수정 지침

### 파일 선택 (Web + Android 공통)
- 파일 바이트는 항상 `withData: true` 로 읽습니다.
- Android 경로(`PlatformFile.path`)에 의존하지 않습니다.

### API 호출
- 모든 API 호출은 `lib/services/api_service.dart` 에서만 수행합니다.
- API Base URL은 `--dart-define=API_BASE` 로 주입합니다. 코드에 하드코딩 금지.

### 상태 관리
- 전역 상태는 `lib/providers/record_provider.dart` (ChangeNotifier) 를 통해서만 관리합니다.
- 페이지 위젯에서 직접 API를 호출하지 않습니다.

### Android 주의
- `android/app/src/main/AndroidManifest.xml` 에 권한 추가 시 사유를 주석으로 명시합니다.
- `usesCleartextTraffic="true"` 는 개발 환경(HTTP)용입니다. 운영 배포 시 HTTPS로 전환해야 합니다.

---

## 6. Git 브랜치 및 커밋 규칙

### 브랜치 구조

```
main          ← 배포 브랜치 (직접 커밋 금지)
kts           ← 통합 개발 브랜치
feature/*     ← 기능 개발 브랜치 (kts 에서 분기)
claude/*      ← 에이전트 작업 브랜치
```

### 커밋 메시지 형식

```
<type>: <요약> (한국어 가능)

<선택적 본문>

https://claude.ai/code/session_...
```

| type | 용도 |
|------|------|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서만 변경 |
| `refactor` | 기능 변경 없는 코드 정리 |
| `chore` | 빌드, 의존성, 설정 변경 |

### 푸시 방법

```bash
git push https://LEEjy0431:<TOKEN>@github.com/LEEjy0431/capstone_music_ver2.git kts
```

---

## 7. 문서 업데이트 규칙

에이전트가 작업을 완료할 때마다 아래를 수행합니다.

1. **`docs/TODO.md`**: 완료된 항목을 ✅ 로 변경하고, 새 항목이 생기면 추가합니다.
2. **`docs/PROGRESS.md`**: 해당 스프린트 섹션에 완료 항목, 결정 사항, 문제 & 해결을 기록합니다.
3. **해당 폴더 README**: 구조나 API가 바뀌면 DFD / 옵션 표 / 트러블슈팅을 업데이트합니다.
4. **루트 `README.md`**: 기술 스택 또는 전체 흐름이 바뀌면 Level 1/2 DFD를 업데이트합니다.

---

## 8. 금지 사항

| 금지 항목 | 이유 |
|-----------|------|
| `module1.py` / `module2.py` 에서 `print()` (stderr 없이) | Go JSON 파싱 오류 |
| `backend/handlers/` 에 CORS 헤더 추가 | 중복, `main.go` 미들웨어로 일원화 |
| `data/` 파일 삭제 또는 교체 | 파이프라인 기본 테스트 파일 |
| API_BASE URL 하드코딩 (`flutter_app/`) | 빌드 환경 분리 불가 |
| `code/environment.yml` 외 경로에 conda 환경 정의 | 환경 파편화 |
| `.env` 파일 커밋 | 키 노출 위험 |
| `main` 브랜치 직접 push | 배포 브랜치 보호 |
