package services

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"path/filepath"
	"runtime"

	"capstone/backend/models"
)

// pythonBin은 OS에 맞는 Python 실행 파일 경로를 반환한다.
func pythonBin() string {
	if runtime.GOOS == "windows" {
		return "python"
	}
	return "python3"
}

// RunPythonAnalysis는 module1→2→3 파이프라인을 subprocess로 실행하고 JSON 결과를 반환한다.
func RunPythonAnalysis(sheetPath, audioPath string) (*models.ScoreResult, error) {
	// main.py 절대 경로: backend/ 기준으로 ../code/main.py
	_, self, _, _ := runtime.Caller(0)
	backendDir := filepath.Join(filepath.Dir(self), "..", "..")
	mainPy := filepath.Join(backendDir, "code", "main.py")
	codeDir := filepath.Join(backendDir, "code")

	cmd := exec.Command(pythonBin(), mainPy,
		"--sheet", sheetPath,
		"--audio", audioPath,
		"--json",
	)
	// Python이 상대경로로 data/를 찾을 수 있도록 작업 디렉토리를 프로젝트 루트로 설정
	cmd.Dir = filepath.Join(codeDir, "..")

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
