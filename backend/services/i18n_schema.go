package services

// feedbackJSONSchema는 OpenAI json_schema 모드에서 사용하는 응답 구조 정의다.
// temperature 0.3 + max_tokens 400 + 이 스키마를 함께 쓰면 파싱 실패율이 거의 0에 수렴한다.
var feedbackJSONSchema = map[string]any{
	"type": "json_schema",
	"json_schema": map[string]any{
		"name":   "piano_feedback",
		"strict": true,
		"schema": map[string]any{
			"type": "object",
			"properties": map[string]any{
				"overall": map[string]any{
					"type":        "string",
					"description": "Overall 2-3 sentence evaluation",
				},
				"pitch": map[string]any{
					"type":        "string",
					"description": "Pitch accuracy feedback, 1-2 sentences",
				},
				"rhythm": map[string]any{
					"type":        "string",
					"description": "Rhythm and beat feedback, 1-2 sentences",
				},
				"timing": map[string]any{
					"type":        "string",
					"description": "Timing deviation feedback, 1-2 sentences",
				},
				"tips": map[string]any{
					"type": "array",
					"items": map[string]any{
						"type": "string",
					},
					"minItems": 2,
					"maxItems": 3,
				},
				"encouragement": map[string]any{
					"type":        "string",
					"description": "One encouraging sentence",
				},
			},
			"required":             []string{"overall", "pitch", "rhythm", "timing", "tips", "encouragement"},
			"additionalProperties": false,
		},
	},
}
