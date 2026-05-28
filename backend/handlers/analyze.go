package handlers

import (
	"encoding/json"
	"io"
	"net/http"
	"os"

	"capstone/backend/models"
	"capstone/backend/services"
)

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

// AnalyzeHandler — POST /api/analyze
//
// multipart/form-data: sheet (xml), audio (wav), lang (ko|en|ja|zh)
//
// 채점(Python 파이프라인)만 실행하고 점수+등급을 즉시 반환한다.
// GPT 피드백은 GET /api/feedback/stream (SSE)으로 별도 수신한다.
//
// Response: { score:{...}, grade:"B+", lang:"ko" }
func AnalyzeHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, models.ErrorResponse{Error: "POST 메서드만 허용됩니다"})
		return
	}

	if err := r.ParseMultipartForm(50 << 20); err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{Error: "파일 파싱 실패: " + err.Error()})
		return
	}

	lang := r.FormValue("lang")
	if lang == "" {
		lang = "ko"
	}

	sheetPath, err := saveUploadedFile(r, "sheet", "*.xml")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{Error: "악보 파일 오류: " + err.Error()})
		return
	}
	defer os.Remove(sheetPath)

	audioPath, err := saveUploadedFile(r, "audio", "*.wav")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{Error: "오디오 파일 오류: " + err.Error()})
		return
	}
	defer os.Remove(audioPath)

	score, err := services.RunPythonAnalysis(sheetPath, audioPath)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, models.ErrorResponse{Error: "분석 실패: " + err.Error()})
		return
	}

	writeJSON(w, http.StatusOK, models.AnalyzeResponse{
		Score: *score,
		Grade: calcGrade(score.Score),
		Lang:  lang,
	})
}

func calcGrade(score float64) string {
	switch {
	case score >= 90:
		return "A"
	case score >= 85:
		return "A-"
	case score >= 80:
		return "B+"
	case score >= 75:
		return "B"
	case score >= 70:
		return "C+"
	default:
		return "C"
	}
}

func saveUploadedFile(r *http.Request, field, pattern string) (string, error) {
	file, _, err := r.FormFile(field)
	if err != nil {
		return "", err
	}
	defer file.Close()

	tmp, err := os.CreateTemp("", pattern)
	if err != nil {
		return "", err
	}
	defer tmp.Close()

	if _, err := io.Copy(tmp, file); err != nil {
		os.Remove(tmp.Name())
		return "", err
	}

	return tmp.Name(), nil
}
