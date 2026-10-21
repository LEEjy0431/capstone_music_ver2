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

// analysisTimeout은 환경변수 ANALYSIS_TIMEOUT_MIN (분 단위) 로 조정 가능.
// 기본값: 20분 (CPU piano_transcription 추론 시간 고려)
func analysisTimeout() time.Duration {
	if v := os.Getenv("ANALYSIS_TIMEOUT_MIN"); v != "" {
		if m, err := fmt.Sscanf(v, "%d", new(int)); m == 1 && err == nil {
			var minutes int
			fmt.Sscanf(v, "%d", &minutes)
			if minutes > 0 {
				return time.Duration(minutes) * time.Minute
			}
		}
	}
	return 20 * time.Minute
}

// RunPythonAnalysis는 module1→2→3 파이프라인을 subprocess로 실행한다.
// 기본 대기 시간: 20분 (ANALYSIS_TIMEOUT_MIN 환경변수로 조정 가능)
func RunPythonAnalysis(sheetPath, audioPath string) (*models.ScoreResult, error) {
	root, err := projectRoot()
	if err != nil {
		return nil, err
	}

	mainPy := filepath.Join(root, "code", "main.py")
	timeout := analysisTimeout()

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, pythonBin(), mainPy,
		"--sheet", sheetPath,
		"--audio", audioPath,
		"--json",
	)
	cmd.Dir = root

	out, err := cmd.Output()
	if ctx.Err() == context.DeadlineExceeded {
		return nil, fmt.Errorf(
			"분석 시간 초과 (%v): 음원이 너무 길거나 CPU가 느립니다. "+
				"ANALYSIS_TIMEOUT_MIN 환경변수로 시간을 늘려주세요 (현재: %.0f분)",
			timeout, timeout.Minutes(),
		)
	}
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			stderr := string(exitErr.Stderr)
			if len(stderr) > 500 {
				stderr = stderr[len(stderr)-500:]
			}
			return nil, fmt.Errorf("python 실행 실패:\n%s", stderr)
		}
		return nil, fmt.Errorf("python 실행 실패: %w", err)
	}

	// stdout에서 JSON 추출 (경고 메시지가 섞일 경우 대비)
	raw := string(out)
	start := -1
	for i, c := range raw {
		if c == '{' {
			start = i
			break
		}
	}
	if start < 0 {
		return nil, fmt.Errorf("JSON 응답 없음 (stdout: %s)", raw[:min(len(raw), 300)])
	}
	raw = raw[start:]

	var result models.ScoreResult
	if err := json.Unmarshal([]byte(raw), &result); err != nil {
		return nil, fmt.Errorf("결과 JSON 파싱 실패: %w\nraw: %s", err, raw[:min(len(raw), 300)])
	}
	if result.Error != "" {
		return nil, fmt.Errorf("분석 오류: %s", result.Error)
	}

	return &result, nil
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
