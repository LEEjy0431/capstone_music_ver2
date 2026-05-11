package services

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"

	"capstone/backend/models"
)

// pythonBin은 OS에 맞는 Python 실행 파일 이름을 반환한다.
func pythonBin() string {
	if runtime.GOOS == "windows" {
		return "python"
	}
	return "python3"
}

// projectRoot는 PROJECT_ROOT 환경변수 → 실행 파일 기준 경로 순으로 탐색한다.
// go run 시에는 실행 파일이 임시 경로에 생성되므로 PROJECT_ROOT를 우선 사용한다.
func projectRoot() (string, error) {
	if root := os.Getenv("PROJECT_ROOT"); root != "" {
		return filepath.Abs(root)
	}

	// 컴파일 바이너리: backend/main → 상위 디렉토리가 프로젝트 루트
	exe, err := os.Executable()
	if err != nil {
		return "", fmt.Errorf("실행 파일 경로 확인 실패: %w", err)
	}
	// backend/main → backend/ → 프로젝트 루트
	root := filepath.Dir(filepath.Dir(exe))
	return filepath.Abs(root)
}

// RunPythonAnalysis는 module1→2→3 파이프라인을 subprocess로 실행하고 JSON 결과를 반환한다.
func RunPythonAnalysis(sheetPath, audioPath string) (*models.ScoreResult, error) {
	root, err := projectRoot()
	if err != nil {
		return nil, err
	}

	mainPy := filepath.Join(root, "code", "main.py")

	cmd := exec.Command(pythonBin(), mainPy,
		"--sheet", sheetPath,
		"--audio", audioPath,
		"--json",
	)
	cmd.Dir = root // Python 상대경로(data/) 기준점

	out, err := cmd.Output()
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
