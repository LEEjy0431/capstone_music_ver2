package services

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"time"

	"capstone/backend/models"
)

const openAIURL = "https://api.openai.com/v1/chat/completions"

var httpClient = &http.Client{Timeout: 120 * time.Second}

type gptRequest struct {
	Model          string         `json:"model"`
	Messages       []gptMessage   `json:"messages"`
	ResponseFormat map[string]any `json:"response_format,omitempty"`
	Temperature    float64        `json:"temperature"`
	MaxTokens      int            `json:"max_tokens,omitempty"`
	Stream         bool           `json:"stream,omitempty"`
}

type gptMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type gptResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
	Error *struct {
		Message string `json:"message"`
	} `json:"error,omitempty"`
}

// ── LLM 백엔드 선택 헬퍼 ─────────────────────────────────────────
// 우선순위: OLLAMA_MODEL 설정 → Ollama(로컬 Qwen)
//           OPENAI_API_KEY 설정 → OpenAI GPT
//           둘 다 없음 → 에러

func llmURL() string {
	if os.Getenv("OLLAMA_MODEL") != "" {
		base := os.Getenv("OLLAMA_BASE_URL")
		if base == "" {
			base = "http://localhost:11434"
		}
		return base + "/v1/chat/completions"
	}
	return openAIURL
}

func llmModel() string {
	if m := os.Getenv("OLLAMA_MODEL"); m != "" {
		return m
	}
	return "gpt-4o-mini"
}

func llmAPIKey() (string, error) {
	if os.Getenv("OLLAMA_MODEL") != "" {
		return "ollama", nil // Ollama는 API 키 불필요
	}
	key := os.Getenv("OPENAI_API_KEY")
	if key == "" {
		return "", fmt.Errorf("OPENAI_API_KEY 또는 OLLAMA_MODEL 환경변수를 설정해주세요")
	}
	return key, nil
}

func isOllama() bool {
	return os.Getenv("OLLAMA_MODEL") != ""
}

// extractJSON은 LLM 응답에서 JSON 블록을 안전하게 추출한다.
// Qwen 같은 소형 모델은 JSON 앞뒤에 텍스트를 붙이는 경우가 있음.
func extractJSON(raw string) string {
	// ```json ... ``` 블록 우선
	re := regexp.MustCompile("(?s)```(?:json)?\\s*(\\{.*?\\})\\s*```")
	if m := re.FindStringSubmatch(raw); len(m) > 1 {
		return m[1]
	}
	// { ... } 블록 추출
	re2 := regexp.MustCompile(`(?s)\{.*\}`)
	if m := re2.FindString(raw); m != "" {
		return m
	}
	return raw
}

// containsCJK는 문자열에 한자/중국어/일본어 문자가 포함됐는지 확인한다.
// Qwen이 한국어 요청에도 한자를 섞는 현상을 감지하기 위해 사용.
func containsCJK(s string) bool {
	for _, r := range s {
		// CJK 통합 한자 (한자, 한자 확장 A/B 포함)
		if (r >= 0x4E00 && r <= 0x9FFF) ||
			(r >= 0x3400 && r <= 0x4DBF) ||
			(r >= 0x20000 && r <= 0x2A6DF) {
			return true
		}
	}
	return false
}

// feedbackContainsCJK는 피드백 구조체의 모든 문자열 필드에 한자가 있는지 확인한다.
func feedbackContainsCJK(f *models.FeedbackResult) bool {
	for _, s := range append(f.Tips, f.Overall, f.Pitch, f.Rhythm, f.Timing, f.Encouragement) {
		if containsCJK(s) {
			return true
		}
	}
	return false
}

// feedbackIsKorean은 피드백에 한글이 포함됐는지 확인한다 (영어로만 응답하는 경우 감지).
func feedbackIsKorean(f *models.FeedbackResult) bool {
	all := f.Overall + f.Pitch + f.Rhythm + f.Timing + f.Encouragement
	for _, s := range f.Tips {
		all += s
	}
	for _, r := range all {
		if r >= 0xAC00 && r <= 0xD7A3 { // 한글 음절
			return true
		}
	}
	return false
}

// callLLM은 단일 LLM 호출을 수행하고 원시 텍스트를 반환한다.
func callLLM(systemPrompt, userPrompt string) (string, error) {
	apiKey, err := llmAPIKey()
	if err != nil {
		return "", err
	}

	req := gptRequest{
		Model: llmModel(),
		Messages: []gptMessage{
			{Role: "system", Content: systemPrompt},
			{Role: "user", Content: userPrompt},
		},
		Temperature: 0.3,
		MaxTokens:   1024,
	}
	if !isOllama() {
		req.ResponseFormat = feedbackJSONSchema
		req.MaxTokens = 700
	}

	reqBody, _ := json.Marshal(req)
	httpReq, err := http.NewRequest("POST", llmURL(), bytes.NewBuffer(reqBody))
	if err != nil {
		return "", err
	}
	httpReq.Header.Set("Authorization", "Bearer "+apiKey)
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := httpClient.Do(httpReq)
	if err != nil {
		return "", fmt.Errorf("LLM API 호출 실패: %w", err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var gptResp gptResponse
	if err := json.Unmarshal(body, &gptResp); err != nil {
		return "", fmt.Errorf("응답 파싱 실패: %w", err)
	}
	if gptResp.Error != nil {
		return "", fmt.Errorf("LLM 오류: %s", gptResp.Error.Message)
	}
	if len(gptResp.Choices) == 0 {
		return "", fmt.Errorf("LLM 응답이 비어있습니다")
	}
	return gptResp.Choices[0].Message.Content, nil
}

// GenerateFeedback는 채점 결과를 LLM에 보내 언어별 피드백을 생성한다.
// OLLAMA_MODEL 설정 시 로컬 Qwen, 없으면 OpenAI GPT를 사용한다.
// 한자 감지 시 최대 2회 재시도한다 (Qwen의 한자 혼입 방지).
func GenerateFeedback(score *models.ScoreResult, lang string) (*models.FeedbackResult, error) {
	systemPrompt, userPrompt := BuildFeedbackPrompt(*score, lang)

	const maxRetry = 2
	var lastErr error

	for attempt := 1; attempt <= maxRetry; attempt++ {
		raw, err := callLLM(systemPrompt, userPrompt)
		if err != nil {
			lastErr = err
			continue
		}

		jsonStr := extractJSON(raw)
		var feedback models.FeedbackResult
		if err := json.Unmarshal([]byte(jsonStr), &feedback); err != nil {
			lastErr = fmt.Errorf("JSON 파싱 실패: %v (raw: %s)", err, raw)
			continue
		}

		// 한국어 요청 시 한자 혼입 또는 한글 미포함 감지 → 재시도
		if lang == "ko" {
			if feedbackContainsCJK(&feedback) {
				lastErr = fmt.Errorf("한자 혼입 감지 (시도 %d/%d)", attempt, maxRetry)
				continue
			}
			if !feedbackIsKorean(&feedback) {
				lastErr = fmt.Errorf("한국어 미포함 — 영어로 응답됨 (시도 %d/%d)", attempt, maxRetry)
				continue
			}
		}

		return &feedback, nil
	}

	return nil, fmt.Errorf("피드백 생성 실패 (최대 %d회 시도): %v", maxRetry, lastErr)
}
