package services

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"capstone/backend/models"
)

const openAIURL = "https://api.openai.com/v1/chat/completions"

var httpClient = &http.Client{Timeout: 60 * time.Second}

type gptRequest struct {
	Model          string         `json:"model"`
	Messages       []gptMessage   `json:"messages"`
	ResponseFormat map[string]any `json:"response_format"`
	Temperature    float64        `json:"temperature"`
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

// GenerateFeedback는 채점 결과를 GPT에 보내 언어별 피드백을 생성한다.
func GenerateFeedback(score *models.ScoreResult, lang string) (*models.FeedbackResult, error) {
	apiKey := os.Getenv("OPENAI_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("OPENAI_API_KEY 환경변수가 설정되지 않았습니다")
	}

	systemPrompt, userPrompt := BuildFeedbackPrompt(*score, lang)

	reqBody, err := json.Marshal(gptRequest{
		Model: "gpt-4o-mini",
		Messages: []gptMessage{
			{Role: "system", Content: systemPrompt},
			{Role: "user", Content: userPrompt},
		},
		ResponseFormat: map[string]any{"type": "json_object"},
		Temperature:    0.7,
	})
	if err != nil {
		return nil, fmt.Errorf("요청 직렬화 실패: %w", err)
	}

	req, err := http.NewRequest("POST", openAIURL, bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, fmt.Errorf("요청 생성 실패: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("GPT API 호출 실패: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("응답 읽기 실패: %w", err)
	}

	var gptResp gptResponse
	if err := json.Unmarshal(body, &gptResp); err != nil {
		return nil, fmt.Errorf("GPT 응답 파싱 실패: %w", err)
	}
	if gptResp.Error != nil {
		return nil, fmt.Errorf("GPT 오류: %s", gptResp.Error.Message)
	}
	if len(gptResp.Choices) == 0 {
		return nil, fmt.Errorf("GPT 응답이 비어있습니다")
	}

	var feedback models.FeedbackResult
	if err := json.Unmarshal([]byte(gptResp.Choices[0].Message.Content), &feedback); err != nil {
		return nil, fmt.Errorf("피드백 JSON 파싱 실패: %w (raw: %s)", err, gptResp.Choices[0].Message.Content)
	}

	return &feedback, nil
}
