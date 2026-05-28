package models

// Python module3 출력 구조체
type ScoreResult struct {
	Score              float64  `json:"score"`
	Correct            int      `json:"correct"`
	Total              int      `json:"total"`
	MissedCount        int      `json:"missed_count"`
	WrongTimingCount   int      `json:"wrong_timing_count"`
	ExtraCount         int      `json:"extra_count"`
	AvgTimingDeviation float64  `json:"avg_timing_deviation"`
	MissedNotes        []any    `json:"missed_notes"`
	WrongTimingNotes   []any    `json:"wrong_timing_notes"`
	ExtraNotes         []any    `json:"extra_notes"`
	Error              string   `json:"error,omitempty"`
}

// GPT가 반환하는 피드백 구조체
type FeedbackResult struct {
	Overall       string   `json:"overall"`
	Pitch         string   `json:"pitch"`
	Rhythm        string   `json:"rhythm"`
	Timing        string   `json:"timing"`
	Tips          []string `json:"tips"`
	Encouragement string   `json:"encouragement"`
}

// /api/analyze 응답 — 채점 결과 + 세션 ID
// GPT 피드백은 GET /api/feedback/stream?session_id=<id> 로 별도 수신한다.
type AnalyzeResponse struct {
	Score     ScoreResult `json:"score"`
	Grade     string      `json:"grade"`
	Lang      string      `json:"lang"`
	SessionID string      `json:"session_id"`
}

// 에러 응답
type ErrorResponse struct {
	Error string `json:"error"`
}
