package models

// NoteDetail은 채점 결과에서 개별 음표 정보를 담는다.
type NoteDetail struct {
	Note     string  `json:"note"`     // 음이름 (예: C4, F#3)
	Pitch    int     `json:"pitch"`    // MIDI 번호
	Start    float64 `json:"start"`    // 시작 시간 (초)
	End      float64 `json:"end"`      // 끝 시간 (초)
	Duration float64 `json:"duration"` // 길이 (초)
	Measure  int     `json:"measure"`  // 마디 번호 (1부터)
}

// Python 채점 파이프라인 출력 구조체
type ScoreResult struct {
	Score              float64 `json:"score"`
	Correct            int     `json:"correct"`
	Total              int     `json:"total"`
	MissedCount        int     `json:"missed_count"`
	WrongTimingCount   int     `json:"wrong_timing_count"`
	ExtraCount         int     `json:"extra_count"`
	AvgTimingDeviation float64 `json:"avg_timing_deviation"`
	BPM                float64 `json:"bpm"`
	// 상세 매칭 내역
	DirectMatched     int `json:"direct_matched"`
	SustainMatched    int `json:"sustain_matched"`
	WideRescued       int `json:"wide_rescued"`
	OctaveRescued     int `json:"octave_rescued"`
	ScoreAwareRescued int `json:"score_aware_rescued"`
	// 화면 표시용 음표 (최대 5개)
	MissedNotes      []any `json:"missed_notes"`
	WrongTimingNotes []any `json:"wrong_timing_notes"`
	ExtraNotes       []any `json:"extra_notes"`
	// AI 피드백용 상세 음표 (최대 20개, 마디 번호 포함)
	MissedNotesDetail []NoteDetail `json:"missed_notes_detail"`
	Error             string       `json:"error,omitempty"`
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
