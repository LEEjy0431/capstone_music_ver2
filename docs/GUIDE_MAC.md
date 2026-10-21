# Mac 개발 환경 가이드

> 대상: macOS (Apple Silicon M1/M2/M3 및 Intel) 팀원  
> 전제: Homebrew, Git 설치 완료

---

## 목차

1. [저장소 클론](#1-저장소-클론)
2. [Python 파이프라인 — Anaconda 환경](#2-python-파이프라인--anaconda-환경)
3. [Go 백엔드 실행](#3-go-백엔드-실행)
4. [Flutter 앱 실행 (Web / Android)](#4-flutter-앱-실행-web--android)
5. [React 프론트엔드 실행 (레거시)](#5-react-프론트엔드-실행-레거시)
6. [환경변수 설정](#6-환경변수-설정)
7. [트러블슈팅](#7-트러블슈팅)

---

## 1. 저장소 클론

```bash
git clone https://github.com/LEEjy0431/capstone_music_ver2.git
cd capstone_music_ver2
git checkout kts
```

---

## 2. Python 파이프라인 — Anaconda 환경

> `code/` 폴더의 분석 파이프라인은 **Anaconda(conda)** 로 환경을 관리합니다.  
> main 브랜치 관리자가 `code/environment.yml` 을 최신 상태로 유지합니다.

### 2-1. Anaconda 설치 (미설치 시)

```bash
# Homebrew로 설치 (권장)
brew install --cask anaconda

# PATH 등록 (zsh 기준)
echo 'export PATH="/opt/homebrew/anaconda3/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

> Intel Mac 경로: `/usr/local/anaconda3/bin`

### 2-2. Apple Silicon — conda 채널 설정

```bash
# arm64 네이티브 패키지를 사용하도록 설정 (M1/M2/M3)
conda config --env --set subdir osx-arm64
```

### 2-3. 환경 생성 (최초 1회)

```bash
# 프로젝트 루트에서 실행
CONDA_SUBDIR=osx-arm64 conda env create -f code/environment.yml   # Apple Silicon
# conda env create -f code/environment.yml                         # Intel Mac
```

### 2-4. 환경 활성화

```bash
conda activate capstone_music
```

### 2-5. macOS 전용 TensorFlow 설치

`code/environment.yml` 의 `tensorflow==2.16.2` 라인은 Linux/Windows 용입니다.  
Mac에서는 **활성화 후** 아래 명령으로 덮어씁니다.

```bash
conda activate capstone_music

# tensorflow 제거 후 macOS 전용 설치
pip uninstall tensorflow -y
pip install tensorflow-macos==2.16.2
pip install tensorflow-metal          # GPU 가속 (선택)
```

### 2-6. 환경 업데이트 (environment.yml 변경 후)

```bash
conda env update -f code/environment.yml --prune
conda activate capstone_music
```

### 2-7. 파이프라인 단독 테스트

```bash
# 환경 활성화 상태에서 실행
python code/main.py \
  --sheet data/piano_sheet_3.xml \
  --audio data/piano_record_3.wav

# JSON 출력 모드 (Go 연동 확인)
python code/main.py \
  --sheet data/piano_sheet_3.xml \
  --audio data/piano_record_3.wav \
  --json
```

---

## 3. Go 백엔드 실행

### 3-1. Go 설치

```bash
brew install go
go version   # go1.21 이상 확인
```

### 3-2. 환경변수 설정

```bash
cp .env.example .env
# .env 파일 편집: OPENAI_API_KEY, PROJECT_ROOT 입력
```

### 3-3. 서버 실행

```bash
# conda 환경이 활성화된 상태에서 실행 (python 경로 인식)
conda activate capstone_music

export OPENAI_API_KEY=sk-...
export PROJECT_ROOT=$(pwd)   # 현재 디렉터리를 프로젝트 루트로 지정

cd backend
go run main.go
```

헬스체크:
```bash
curl http://localhost:8080/health
# {"status":"ok"}
```

---

## 4. Flutter 앱 실행 (Web / Android)

### 4-1. Flutter SDK 설치

```bash
brew install --cask flutter
flutter doctor    # 필수 항목 모두 ✓ 확인
```

> Android 빌드가 필요하면 Android Studio도 설치하세요.

### 4-2. 의존성 설치

```bash
cd flutter_app
flutter pub get
```

### 4-3. Web 실행

```bash
flutter run -d chrome \
  --dart-define=API_BASE=http://localhost:8080
```

### 4-4. Android 실행

```bash
# 에뮬레이터 또는 실기기 연결 후
flutter run -d android \
  --dart-define=API_BASE=http://<Mac-IP>:8080
```

> Mac IP 확인: `ipconfig getifaddr en0`

### 4-5. 빌드

```bash
# Web 정적 파일
flutter build web --dart-define=API_BASE=http://localhost:8080

# Android APK
flutter build apk --release --dart-define=API_BASE=http://<서버IP>:8080
```

---

## 5. React 프론트엔드 실행 (레거시)

> `src/` 의 React 앱은 Flutter 전환 전 MVP 검증용으로 유지됩니다.

```bash
# 프로젝트 루트에서
npm install
npm run dev
# http://localhost:5173 접속
```

---

## 6. 환경변수 설정

`.env` 파일 (프로젝트 루트에 생성):

```bash
cp .env.example .env
```

| 변수 | 필수 | 예시 | 설명 |
|------|------|------|------|
| `OPENAI_API_KEY` | ✅ | `sk-...` | OpenAI API 키 |
| `PROJECT_ROOT` | ✅ | `/Users/name/capstone_music_ver2` | 프로젝트 절대 경로 |
| `PORT` | | `8080` | Go 서버 포트 |
| `VITE_API_BASE` | | `http://localhost:8080` | React 개발 서버용 |

> `.env` 파일은 `.gitignore`에 포함되어 있으므로 커밋되지 않습니다.

---

## 7. 트러블슈팅

### `conda: command not found`
```bash
# PATH 재설정
export PATH="/opt/homebrew/anaconda3/bin:$PATH"   # Apple Silicon
export PATH="/usr/local/anaconda3/bin:$PATH"       # Intel
source ~/.zshrc
```

### `tensorflow` 설치 오류 (Apple Silicon)
```bash
pip uninstall tensorflow tensorflow-macos -y
pip install tensorflow-macos==2.16.2
```

### `piano_transcription_inference` 설치 오류
```bash
# conda 환경에서 pip로 재설치
conda activate capstone_music
pip install piano-transcription-inference==0.0.6
```

### `onnxruntime` arm64 오류
```bash
pip uninstall onnxruntime -y
pip install onnxruntime-silicon   # Apple Silicon 전용
```

### Go 서버에서 `python3: command not found`
```bash
# conda 환경이 활성화된 상태로 Go 서버를 실행해야 합니다.
conda activate capstone_music
which python3   # 경로 확인
cd backend && go run main.go
```

### `PROJECT_ROOT` 경로 오류
```bash
# 절대 경로로 설정 (상대 경로 사용 금지)
export PROJECT_ROOT=/Users/$(whoami)/capstone_music_ver2
```

### Flutter `doctor` 경고 — Android SDK 없음
Android 빌드가 불필요한 경우 Web만 사용합니다.  
Android 빌드가 필요한 경우 Android Studio를 설치하세요.
```bash
brew install --cask android-studio
flutter doctor --android-licenses
```

### CORS 오류 (Flutter Web → Go)
Go 서버가 실행 중인지, `backend/main.go` 의 `corsHandler` 가 `mux` 전체를 감싸고 있는지 확인합니다.
```bash
curl -X OPTIONS http://localhost:8080/api/analyze \
  -H "Origin: http://localhost:*" -v
# < HTTP/1.1 204 No Content 응답 확인
```
