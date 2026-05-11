package handlers

import (
	"net/http"
	"strconv"

	"capstone/backend/models"
	"capstone/backend/services"
)

// FeedbackStreamHandler는 GET /api/feedback/stream 을 처리한다.
//
// Query Parameters:
//
//	score          float  채점 점수 (0~100)
//	correct        int    정확한 음표 수
//	total          int    전체 음표 수
//	missed         int    누락 음표 수
//	timing_errors  int    박자 오류 수
//	extra          int    여분 음표 수
//	avg_dev        float  평균 타이밍 편차(초)
//	lang           string 피드백 언어 (ko|en|ja|zh), 기본값 ko
//
// SSE Response:
//
//	event: chunk   data: {"type":"chunk","text":"..."}
//	event: done    data: {"type":"done","feedback":{...}}
//	event: error   data: {"type":"error","error":"..."}
//
// 사용 예 (채점 완료 후 별도 SSE 호출):
//
//	GET /api/feedback/stream?score=83.5&correct=67&total=80&missed=8&timing_errors=5&extra=2&avg_dev=0.087&lang=ko
func FeedbackStreamHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, models.ErrorResponse{Error: "GET 메서드만 허용됩니다"})
		return
	}

	q := r.URL.Query()

	score := models.ScoreResult{
		Score:              parseFloat(q.Get("score")),
		Correct:            parseInt(q.Get("correct")),
		Total:              parseInt(q.Get("total")),
		MissedCount:        parseInt(q.Get("missed")),
		WrongTimingCount:   parseInt(q.Get("timing_errors")),
		ExtraCount:         parseInt(q.Get("extra")),
		AvgTimingDeviation: parseFloat(q.Get("avg_dev")),
	}

	lang := q.Get("lang")
	if lang == "" {
		lang = "ko"
	}

	services.GenerateFeedbackStream(w, &score, lang)
}

func parseFloat(s string) float64 {
	v, _ := strconv.ParseFloat(s, 64)
	return v
}

func parseInt(s string) int {
	v, _ := strconv.Atoi(s)
	return v
}
