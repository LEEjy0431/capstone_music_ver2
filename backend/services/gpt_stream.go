package services

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"capstone/backend/models"
)

// StreamEvent는 SSE 클라이언트로 전달하는 이벤트 단위다.
type StreamEvent struct {
	Type     string                `json:"type"`              // "chunk" | "done" | "error"
	Text     string                `json:"text,omitempty"`    // chunk: 누적 텍스트 조각
	Feedback *models.FeedbackResult `json:"feedback,omitempty"` // done: 완성된 피드백
	Error    string                `json:"error,omitempty"`   // error: 오류 메시지
}

// streamChunk는 OpenAI SSE 응답의 단일 delta 청크다.
type streamChunk struct {
	Choices []struct {
		Delta struct {
			Content string `json:"content"`
		} `json:"delta"`
		FinishReason *string `json:"finish_reason"`
	} `json:"choices"`
	Error *struct {
		Message string `json:"message"`
	} `json:"error,omitempty"`
}

// streamClient는 스트리밍 전용 HTTP 클라이언트 (타임아웃 없음)
var streamClient = &http.Client{Timeout: 0}

// GenerateFeedbackStream은 GPT 응답을 SSE로 스트리밍한다.
// w에 "event: chunk\ndata: {...}\n\n" 형식으로 청크를 쓰고,
// 완료 시 "event: done\ndata: {...feedback JSON...}\n\n" 을 전송한다.
//
// 호출 예: GET /api/feedback/stream
func GenerateFeedbackStream(w http.ResponseWriter, score *models.ScoreResult, lang string) {
	apiKey := os.Getenv("OPENAI_API_KEY")
	if apiKey == "" {
		writeSSEEvent(w, StreamEvent{Type: "error", Error: "OPENAI_API_KEY 미설정"})
		return
	}

	flusher, ok := w.(http.Flusher)
	if !ok {
		writeSSEEvent(w, StreamEvent{Type: "error", Error: "스트리밍 미지원 클라이언트"})
		return
	}

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no") // nginx 버퍼링 비활성화

	systemPrompt, userPrompt := BuildFeedbackPrompt(*score, lang)

	reqBody, err := json.Marshal(gptRequest{
		Model: "gpt-4o-mini",
		Messages: []gptMessage{
			{Role: "system", Content: systemPrompt},
			{Role: "user", Content: userPrompt},
		},
		ResponseFormat: feedbackJSONSchema,
		Temperature:    0.3,
		MaxTokens:      400,
		Stream:         true,
	})
	if err != nil {
		writeSSEEvent(w, StreamEvent{Type: "error", Error: "요청 직렬화 실패: " + err.Error()})
		return
	}

	req, err := http.NewRequest("POST", openAIURL, bytes.NewBuffer(reqBody))
	if err != nil {
		writeSSEEvent(w, StreamEvent{Type: "error", Error: "요청 생성 실패: " + err.Error()})
		return
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")

	ctx := req.Context()
	req = req.WithContext(ctx)

	resp, err := streamClient.Do(req)
	if err != nil {
		writeSSEEvent(w, StreamEvent{Type: "error", Error: "GPT API 호출 실패: " + err.Error()})
		return
	}
	defer resp.Body.Close()

	var fullText strings.Builder
	scanner := bufio.NewScanner(resp.Body)
	scanner.Buffer(make([]byte, 64*1024), 64*1024)

	for scanner.Scan() {
		line := scanner.Text()

		if !strings.HasPrefix(line, "data: ") {
			continue
		}

		payload := strings.TrimPrefix(line, "data: ")
		if payload == "[DONE]" {
			break
		}

		var chunk streamChunk
		if err := json.Unmarshal([]byte(payload), &chunk); err != nil {
			continue
		}
		if chunk.Error != nil {
			writeSSEEvent(w, StreamEvent{Type: "error", Error: chunk.Error.Message})
			return
		}
		if len(chunk.Choices) == 0 {
			continue
		}

		delta := chunk.Choices[0].Delta.Content
		if delta == "" {
			continue
		}

		fullText.WriteString(delta)

		writeSSEEvent(w, StreamEvent{Type: "chunk", Text: delta})
		flusher.Flush()
	}

	if err := scanner.Err(); err != nil {
		writeSSEEvent(w, StreamEvent{Type: "error", Error: "스트림 읽기 오류: " + err.Error()})
		return
	}

	// 스트리밍 완료 후 누적된 JSON을 파싱하여 done 이벤트로 전송
	var feedback models.FeedbackResult
	if err := json.Unmarshal([]byte(fullText.String()), &feedback); err != nil {
		writeSSEEvent(w, StreamEvent{
			Type:  "error",
			Error: fmt.Sprintf("피드백 JSON 파싱 실패: %v (raw: %s)", err, fullText.String()),
		})
		return
	}

	writeSSEEvent(w, StreamEvent{Type: "done", Feedback: &feedback})
	flusher.Flush()
}

// writeSSEEvent는 단일 SSE 이벤트를 ResponseWriter에 기록한다.
func writeSSEEvent(w http.ResponseWriter, evt StreamEvent) {
	data, _ := json.Marshal(evt)
	fmt.Fprintf(w, "event: %s\ndata: %s\n\n", evt.Type, data)
	if f, ok := w.(http.Flusher); ok {
		f.Flush()
	}
}

// keepAlive는 분석 대기 중 SSE 연결을 유지하는 heartbeat를 전송한다.
// Go routine으로 실행하고 done 채널로 종료한다.
func KeepAliveSSE(w http.ResponseWriter, done <-chan struct{}) {
	flusher, ok := w.(http.Flusher)
	if !ok {
		return
	}
	ticker := time.NewTicker(15 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-done:
			return
		case <-ticker.C:
			fmt.Fprintf(w, ": heartbeat\n\n")
			flusher.Flush()
		}
	}
}
