@echo off
REM ===============================================================
REM  capstone_music_ver2  - Windows one-click runner
REM  - conda 환경 (capstone-music-windows) 자동 생성/활성화
REM  - 의존성 설치 (최초 1회만)
REM  - code\main.py 실행
REM ===============================================================

setlocal ENABLEDELAYEDEXPANSION

set "PROJECT_DIR=%~dp0"
set "ENV_NAME=capstone-music-windows"
set "INSTALL_MARKER=%PROJECT_DIR%.install_done"

cd /d "%PROJECT_DIR%"

REM --- 1) conda 존재 여부 확인 -----------------------------------
where conda >nul 2>&1
if errorlevel 1 (
    echo [ERROR] conda 가 PATH 에 없습니다.
    echo Anaconda Prompt 를 사용하거나, Miniconda/Anaconda 를 설치한 뒤 다시 실행해 주세요.
    echo 다운로드: https://docs.conda.io/projects/miniconda/en/latest/
    pause
    exit /b 1
)

REM --- 2) conda 활성화 훅 로드 (cmd 에서 conda activate 가능하게) ---
for /f "delims=" %%i in ('where conda') do set "CONDA_EXE=%%i"
for %%I in ("%CONDA_EXE%") do set "CONDA_DIR=%%~dpI.."
call "%CONDA_DIR%\condabin\conda.bat" activate base >nul 2>&1

REM --- 3) 환경 존재 확인, 없으면 생성 -----------------------------
call conda env list | findstr /C:"%ENV_NAME%" >nul
if errorlevel 1 (
    echo [INFO] conda 환경 "%ENV_NAME%" 을(를) 생성합니다. 시간이 걸릴 수 있습니다...
    call conda env create -f "%PROJECT_DIR%environment-windows.yml"
    if errorlevel 1 (
        echo [ERROR] conda 환경 생성에 실패했습니다.
        pause
        exit /b 1
    )
) else (
    echo [INFO] conda 환경 "%ENV_NAME%" 이(가) 이미 존재합니다.
)

REM --- 4) 환경 활성화 -------------------------------------------
call conda activate %ENV_NAME%
if errorlevel 1 (
    echo [ERROR] conda 환경 활성화 실패: %ENV_NAME%
    pause
    exit /b 1
)

REM --- 5) pip 패키지 설치 (최초 1회만) --------------------------
if not exist "%INSTALL_MARKER%" (
    echo [INFO] pip 패키지를 설치합니다...
    python -m pip install --upgrade pip
    pip install -r "%PROJECT_DIR%requirements-windows.txt"
    if errorlevel 1 (
        echo [ERROR] pip 패키지 설치 실패. requirements-windows.txt 를 확인해 주세요.
        pause
        exit /b 1
    )
    echo done> "%INSTALL_MARKER%"
) else (
    echo [INFO] pip 패키지가 이미 설치되어 있습니다. (재설치하려면 .install_done 파일 삭제)
)

REM --- 6) main.py 실행 ------------------------------------------
echo.
echo [INFO] code\main.py 실행
echo ===============================================================
python "%PROJECT_DIR%code\main.py"
set "EXIT_CODE=%ERRORLEVEL%"

echo ===============================================================
echo [INFO] 종료 코드: %EXIT_CODE%
pause
exit /b %EXIT_CODE%
