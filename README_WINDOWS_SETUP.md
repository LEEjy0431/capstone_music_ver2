# Windows 환경 셋업 & 실행 가이드

이 프로젝트는 macOS 에서 처음 만들어졌으며, Windows 팀원이 그대로 실행할 수 있도록
다음과 같은 환경 구성 파일이 함께 제공됩니다.

| 파일 | 용도 |
| --- | --- |
| `environment-windows.yml` | conda 환경 정의 (Python 3.11 + 네이티브 라이브러리 + PyTorch CPU) |
| `requirements-windows.txt` | conda 로 못 깐 순수 파이썬 패키지 (pip 설치) |
| `run.bat` | 환경 생성 → 패키지 설치 → `code\main.py` 실행을 한 번에 |

---

## 0. 사전 준비

Miniconda(또는 Anaconda) 가 설치되어 있어야 합니다.
Miniconda 다운로드: <https://docs.conda.io/projects/miniconda/en/latest/>

> 설치할 때 "Add Miniconda3 to my PATH environment variable" 옵션을 켜거나,
> 그렇지 않다면 항상 **Anaconda Prompt** 에서 `run.bat` 을 실행해 주세요.

---

## 1. 가장 쉬운 방법 — `run.bat` 더블클릭 (또는 실행)

프로젝트 루트(이 README 가 있는 폴더)에서:

```powershell
run.bat
```

`run.bat` 이 자동으로 수행하는 작업:

1. `conda` 가 PATH 에 있는지 확인
2. `capstone-music-windows` conda 환경이 없으면 `environment-windows.yml` 로 생성
3. 환경 활성화
4. (최초 1회) `requirements-windows.txt` 의 pip 패키지 설치
5. `python code\main.py` 실행

설치가 한 번 끝나면 `.install_done` 마커 파일이 만들어져, 두 번째 실행부터는
바로 `main.py` 가 실행됩니다. 패키지를 다시 설치하려면 `.install_done` 파일을 지우면 됩니다.

---

## 2. 수동으로 단계별 실행하고 싶다면

```powershell
REM 1) 환경 생성 (최초 1회)
conda env create -f environment-windows.yml

REM 2) 환경 활성화
conda activate capstone-music-windows

REM 3) pip 패키지 설치 (최초 1회)
pip install -r requirements-windows.txt

REM 4) 실행
python code\main.py
```

---

## 3. GPU(CUDA) 사용을 원할 경우

`environment-windows.yml` 은 기본적으로 `cpuonly` PyTorch 를 설치합니다.
CUDA 환경에서 가속하려면 환경 생성 후 PyTorch 만 재설치하세요:

```powershell
conda activate capstone-music-windows
conda remove pytorch torchvision torchaudio cpuonly -y
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```

그리고 `code\module2.py` 의 `PianoTranscription(device='cpu')` 를 `'cuda'` 로 변경합니다.

---

## 4. 자주 만나는 문제

- **`conda 가 PATH 에 없습니다.`**
  - Anaconda Prompt 에서 `run.bat` 을 실행하세요.

- **`pip install` 도중 빌드 오류**
  - `numba`, `llvmlite`, `soundfile`, `soxr`, `fluidsynth` 같은 라이브러리는
    이미 conda 에서 바이너리로 설치되도록 잡아 두었습니다.
    그래도 실패한다면 오류 메시지 전체를 공유해 주세요.

- **`piano_transcription_inference` 모델 다운로드 진행이 멈춤**
  - 최초 실행 시 사전학습 모델(약 200MB) 을 자동 다운로드합니다. 네트워크 환경을 확인해 주세요.

- **`FileNotFoundError: data/piano_sheet_3.xml`**
  - `code\main.py` 는 스크립트 기준 절대경로로 데이터를 읽도록 수정되어 있습니다.
    그래도 발생한다면 `data\` 폴더의 파일이 git 에 정상적으로 올라왔는지 확인해 주세요.

---

## 5. 참고: 기존 `requirements.txt` 와의 관계

`requirements.txt` 는 macOS 환경에서 `pip freeze` 로 추출된 핀 파일이라
Windows 휠과 충돌하는 경우가 있습니다. Windows 에서는 `requirements-windows.txt` 를
사용해 주세요. macOS 팀원의 환경에는 영향을 주지 않습니다.
