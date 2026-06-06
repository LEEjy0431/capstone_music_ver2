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

// GenerateFeedback는 채점 결과를 LLM에 보내 언어별 피드백을 생성한다.
// OLLAMA_MODEL 설정 시 로컬 Qwen, 없으면 OpenAI GPT를 사용한다.
func GenerateFeedback(score *models.ScoreResult, lang string) (*models.FeedbackResult, error) {
	apiKey, err := llmAPIKey()
	if err != nil {
		return nil, err
	}

	systemPrompt, userPrompt := BuildFeedbackPrompt(*score, lang)

	req := gptRequest{
		Model: llmModel(),
		Messages: []gptMessage{
			{Role: "system", Content: systemPrompt},
			{Role: "user", Content: userPrompt},
		},
		Temperature: 0.4,
		MaxTokens:   1024,
	}

	// OpenAI만 JSON 모드 지원 (Qwen/Ollama는 프롬프트로 JSON 유도)
	if !isOllama() {
		req.ResponseFormat = feedbackJSONSchema
		req.MaxTokens = 700
	}

	reqBody, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("요청 직렬화 실패: %w", err)
	}

	httpReq, err := http.NewRequest("POST", llmURL(), bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, fmt.Errorf("요청 생성 실패: %w", err)
	}
	httpReq.Header.Set("Authorization", "Bearer "+apiKey)
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("LLM API 호출 실패: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("응답 읽기 실패: %w", err)
	}

	var gptResp gptResponse
	if err := json.Unmarshal(body, &gptResp); err != nil {
		return nil, fmt.Errorf("LLM 응답 파싱 실패: %w", err)
	}
	if gptResp.Error != nil {
		return nil, fmt.Errorf("LLM 오류: %s", gptResp.Error.Message)
	}
	if len(gptResp.Choices) == 0 {
		return nil, fmt.Errorf("LLM 응답이 비어있습니다")
	}

	raw := gptResp.Choices[0].Message.Content
	jsonStr := extractJSON(raw)

	var feedback models.FeedbackResult
	if err := json.Unmarshal([]byte(jsonStr), &feedback); err != nil {
		return nil, fmt.Errorf("피드백 JSON 파싱 실패: %v (raw: %s)", err, raw)
	}

	return &feedback, nil
}
