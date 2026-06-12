package handlers

import (
	"net/http"

	"capstone/backend/models"
	"capstone/backend/services"
)

// FeedbackStreamHandler는 GET /api/feedback/stream 을 처리한다.
//
// Query Parameters:
//
//	session_id  string  POST /api/analyze 응답에서 받은 세션 ID (유효시간 5분)
//	lang        string  피드백 언어 (ko|en|ja|zh), 기본값 ko
//
// SSE Response:
//
//	event: chunk   data: {"type":"chunk","text":"..."}
//	event: done    data: {"type":"done","feedback":{...}}
//	event: error   data: {"type":"error","error":"..."}
//
// 사용 흐름:
//
//	1. POST /api/analyze → { score, grade, lang, session_id } 수신
//	2. GET /api/feedback/stream?session_id=<id>&lang=ko → SSE 피드백 수신
func FeedbackStreamHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, models.ErrorResponse{Error: "GET 메서드만 허용됩니다"})
		return
	}

	q := r.URL.Query()
	sessionID := q.Get("session_id")
	if sessionID == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{Error: "session_id가 필요합니다"})
		return
	}

	score, ok := services.GetScore(sessionID)
	if !ok {
		writeJSON(w, http.StatusNotFound, models.ErrorResponse{Error: "세션을 찾을 수 없습니다 (만료되었거나 존재하지 않음)"})
		return
	}

	lang := q.Get("lang")
	if lang == "" {
		lang = "ko"
	}

	services.GenerateFeedbackStream(w, &score, lang)
}
