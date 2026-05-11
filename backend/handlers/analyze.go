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

func corsMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next(w, r)
	}
}

// AnalyzeHandler는 POST /api/analyze 요청을 처리한다.
// multipart/form-data: sheet (xml), audio (wav), lang (ko|en|ja|zh)
func AnalyzeHandler(w http.ResponseWriter, r *http.Request) {
	corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
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

		feedback, err := services.GenerateFeedback(score, lang)
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, models.ErrorResponse{Error: "피드백 생성 실패: " + err.Error()})
			return
		}

		writeJSON(w, http.StatusOK, models.AnalyzeResponse{
			Score:    *score,
			Feedback: *feedback,
			Grade:    calcGrade(score.Score),
			Lang:     lang,
		})
	})(w, r)
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

// saveUploadedFile은 multipart 필드를 임시 파일로 저장하고 경로를 반환한다.
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
