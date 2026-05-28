package services

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"

	"capstone/backend/models"
)

// pythonBin은 실행할 Python 경로를 반환한다.
// 우선순위: PYTHON_CMD 환경변수 → OS 기본값
//
// macOS Anaconda 사용 시 .env에 전체 경로를 지정한다:
//
//	PYTHON_CMD=/opt/homebrew/anaconda3/envs/capstone_music/bin/python3
func pythonBin() string {
	if cmd := os.Getenv("PYTHON_CMD"); cmd != "" {
		return cmd
	}
	if runtime.GOOS == "windows" {
		return "python"
	}
	return "python3"
}

// projectRoot는 PROJECT_ROOT 환경변수 → 실행 파일 기준 경로 순으로 탐색한다.
func projectRoot() (string, error) {
	if root := os.Getenv("PROJECT_ROOT"); root != "" {
		return filepath.Abs(root)
	}
	exe, err := os.Executable()
	if err != nil {
		return "", fmt.Errorf("실행 파일 경로 확인 실패: %w", err)
	}
	// backend/main → backend/ → 프로젝트 루트
	root := filepath.Dir(filepath.Dir(exe))
	return filepath.Abs(root)
}

// RunPythonAnalysis는 module1→2→3 파이프라인을 subprocess로 실행한다.
// 최대 대기 시간: 5분 (piano_transcription 모델 추론 시간 고려)
func RunPythonAnalysis(sheetPath, audioPath string) (*models.ScoreResult, error) {
	root, err := projectRoot()
	if err != nil {
		return nil, err
	}

	mainPy := filepath.Join(root, "code", "main.py")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	cmd := exec.CommandContext(ctx, pythonBin(), mainPy,
		"--sheet", sheetPath,
		"--audio", audioPath,
		"--json",
	)
	cmd.Dir = root // Python 상대경로(data/) 기준점

	out, err := cmd.Output()
	if ctx.Err() == context.DeadlineExceeded {
		return nil, fmt.Errorf("분석 시간 초과 (5분): piano_transcription 모델 추론이 너무 오래 걸립니다")
	}
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("python 실행 실패: %s", string(exitErr.Stderr))
		}
		return nil, fmt.Errorf("python 실행 실패: %w", err)
	}

	var result models.ScoreResult
	if err := json.Unmarshal(out, &result); err != nil {
		return nil, fmt.Errorf("결과 JSON 파싱 실패: %w (raw: %s)", err, string(out))
	}
	if result.Error != "" {
		return nil, fmt.Errorf("분석 오류: %s", result.Error)
	}

	return &result, nil
}
