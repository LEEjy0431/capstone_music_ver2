package services

import (
	"fmt"

	"capstone/backend/models"
)

// SupportedLangs는 lang 코드 → 언어 명칭 매핑이다.
var SupportedLangs = map[string]string{
	"ko": "한국어",
	"en": "English",
	"ja": "日本語",
	"zh": "中文",
}

// NormalizeLang은 지원하지 않는 언어 코드를 기본값(ko)으로 정규화한다.
func NormalizeLang(lang string) string {
	if _, ok := SupportedLangs[lang]; ok {
		return lang
	}
	return "ko"
}

// BuildFeedbackPrompt는 채점 결과와 언어 코드를 받아 GPT system/user 프롬프트를 생성한다.
func BuildFeedbackPrompt(score models.ScoreResult, lang string) (system, user string) {
	lang = NormalizeLang(lang)
	langName := SupportedLangs[lang]

	system = fmt.Sprintf(`You are an expert piano teacher providing constructive and encouraging feedback.
Based on the performance analysis data, generate specific and motivating feedback for the student.
You MUST respond ONLY in %s (%s).
You MUST respond ONLY in valid JSON with exactly this structure, no extra text:
{
  "overall": "2-3 sentence overall evaluation",
  "pitch": "1-2 sentence pitch accuracy feedback",
  "rhythm": "1-2 sentence rhythm/beat feedback",
  "timing": "1-2 sentence timing feedback",
  "tips": ["improvement tip 1", "improvement tip 2", "improvement tip 3"],
  "encouragement": "1 sentence encouraging message"
}`, langName, lang)

	user = fmt.Sprintf(`Piano performance analysis result:
- Final score: %.1f / 100
- Correct notes: %d / %d
- Missed notes: %d
- Timing errors: %d
- Extra (unintended) notes: %d
- Average timing deviation: %.3f seconds

Generate the feedback JSON based on this data.`,
		score.Score, score.Correct, score.Total,
		score.MissedCount, score.WrongTimingCount,
		score.ExtraCount, score.AvgTimingDeviation,
	)

	return
}
