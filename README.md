# 피아노 연주 자동 평가 시스템

악보(정답)와 연주 WAV를 비교해 점수를 매기는 자동 채점 시스템입니다.

## 지원 입력 형식

| 형식 | 확장자 |
|------|--------|
| 악보 이미지 | `.png` `.jpg` `.jpeg` `.pdf` |
| 악보 데이터 | `.xml` `.musicxml` `.mxl` `.mid` `.midi` |
| 연주 오디오 | `.wav` |

---

## 설치 방법

### 1. Python 가상환경 생성 (권장)

```bash
python -m venv capstone_env
source capstone_env/bin/activate        # macOS / Linux
capstone_env\Scripts\activate           # Windows
```

### 2. Python 패키지 설치

**macOS:**
```bash
pip install -r requirements.txt
```

**Windows / Linux:**
```bash
pip install -r requirements-general.txt
```

### 3. Audiveris 설치 (PNG / JPEG / PDF 악보 처리 시 필수)

Audiveris는 악보 이미지를 MusicXML로 변환하는 OMR(광학 악보 인식) 도구입니다.

- 다운로드: https://github.com/Audiveris/audiveris/releases
- Java 11 이상이 필요합니다: https://adoptium.net

**macOS:**
1. 위 링크에서 `.dmg` 다운로드 후 `/Applications/Audiveris.app` 에 설치

**Windows / Linux:**
1. `.zip` 다운로드 후 압축 해제
2. `bin/audiveris` (또는 `audiveris.bat`)를 PATH에 추가

> XML / MIDI 형식 악보만 사용한다면 Audiveris 설치 없이도 동작합니다.

---

## 실행 방법

```bash
# 기본 실행 (data/piano_sheet_3.png + data/piano_record_3.wav)
python code/main.py

# 파일 직접 지정
python code/main.py data/my_sheet.xml data/my_recording.wav
python code/main.py data/my_sheet.png data/my_recording.wav
python code/main.py data/my_sheet.pdf data/my_recording.wav
```

### 실행 위치 주의

반드시 **프로젝트 루트**에서 실행해야 합니다:

```bash
# 올바른 실행 위치
cd capstone_music_ver2
python code/main.py

# 잘못된 예 (data/ 경로를 못 찾음)
cd capstone_music_ver2/code
python main.py
```

---

## 출력 예시

```
=== 피아노 연주 자동 평가 시스템 ===

1. 정답 악보 분석 중...
2. 연주 WAV 분석 중 (트랜스크립션)...
3. 1차 채점 (5단계 매칭)...
4. Score-aware audio 검증...

============================================
             최종 채점 결과
============================================
점수:              87.5점 / 100점
정확한 음표:       70 / 80개
  ├─ 직접 매칭:    60개
  ├─ 지속음 매칭:  5개
  ├─ 와이드 구제:  3개
  ├─ 옥타브 구제:  1개
  └─ Audio 검증:   1개
실제 누락:         10개
여분의 음표:       3개
평균 timing 오차:  0.045초
```

---

## 프로젝트 구조

```
capstone_music_ver2/
├── code/
│   ├── main.py          # 진입점
│   ├── module1.py       # 악보 분석 (XML / 이미지 / PDF)
│   ├── module2.py       # 오디오 트랜스크립션
│   ├── module3.py       # 음표 비교 및 채점
│   └── chord_upgrade.py # Score-aware 검증
├── data/                # 악보 및 WAV 파일 (직접 준비)
├── requirements.txt          # macOS용 패키지 목록
├── requirements-general.txt  # Windows/Linux용 패키지 목록
└── README.md
```

---

## 문제 해결

### Audiveris가 없을 때 이미지/PDF 처리 불가
→ Audiveris를 설치하거나, 악보를 XML 또는 MIDI 형식으로 변환해서 사용하세요.

### `piano_transcription_inference` 관련 오류
모델 파일이 자동 다운로드됩니다. 첫 실행 시 인터넷 연결이 필요합니다.

### `tensorflow` 설치 오류 (Windows)
```bash
pip install tensorflow
```
`tensorflow-macos`는 macOS 전용이므로 Windows에서는 `tensorflow`를 사용하세요.
