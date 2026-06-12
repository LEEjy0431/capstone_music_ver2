package services

// feedbackJSONSchema는 OpenAI json_schema strict 모드 응답 구조 정의다.
// strict: true 일 때는 minItems/maxItems/minimum 등 미지원 키워드 제거 필수.
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
					"description": "Overall 2-3 sentence evaluation of the performance",
				},
				"pitch": map[string]any{
					"type":        "string",
					"description": "Pitch accuracy feedback in 1-2 sentences",
				},
				"rhythm": map[string]any{
					"type":        "string",
					"description": "Rhythm and beat consistency feedback in 1-2 sentences",
				},
				"timing": map[string]any{
					"type":        "string",
					"description": "Timing deviation and note onset accuracy in 1-2 sentences",
				},
				"tips": map[string]any{
					"type": "array",
					"items": map[string]any{
						"type": "string",
					},
				},
				"encouragement": map[string]any{
					"type":        "string",
					"description": "One warm, encouraging sentence to motivate the student",
				},
			},
			"required":             []string{"overall", "pitch", "rhythm", "timing", "tips", "encouragement"},
			"additionalProperties": false,
		},
	},
}
