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

// gradeLabel은 점수를 등급 문자열로 변환한다.
func gradeLabel(score float64) string {
	switch {
	case score >= 95:
		return "A+ (excellent)"
	case score >= 90:
		return "A (great)"
	case score >= 85:
		return "A- (good)"
	case score >= 80:
		return "B+ (above average)"
	case score >= 75:
		return "B (average)"
	case score >= 70:
		return "C+ (needs work)"
	default:
		return "C (needs significant improvement)"
	}
}

// BuildFeedbackPrompt는 채점 결과와 언어 코드를 받아 GPT system/user 프롬프트를 생성한다.
func BuildFeedbackPrompt(score models.ScoreResult, lang string) (system, user string) {
	lang = NormalizeLang(lang)
	langName := SupportedLangs[lang]

	system = fmt.Sprintf(
		"You are an experienced piano teacher providing detailed, constructive performance feedback. "+
			"Always respond ONLY in %s (%s).\n"+
			"You MUST respond with ONLY a valid JSON object. No explanation, no markdown, no extra text before or after the JSON.\n"+
			"The JSON must have exactly these keys: overall, pitch, rhythm, timing, tips (array of 2-3 strings), encouragement.",
		langName, lang,
	)

	// 누락률 / 여분음 비율 계산
	missedPct := 0.0
	extraPct := 0.0
	if score.Total > 0 {
		missedPct = float64(score.MissedCount) / float64(score.Total) * 100
		extraPct = float64(score.ExtraCount) / float64(score.Total) * 100
	}

	user = fmt.Sprintf(
		"Piano performance analysis result:\n"+
			"- Overall score: %.1f/100 (Grade: %s)\n"+
			"- Notes played correctly: %d out of %d total (%.1f%%)\n"+
			"- Missed notes: %d (%.1f%% of total)\n"+
			"- Timing errors: %d notes with wrong onset time\n"+
			"- Extra notes (not in score): %d (%.1f%%)\n"+
			"- Average timing deviation: %.3f seconds\n\n"+
			"Based on these metrics, provide specific and helpful feedback. "+
			"Include 2-3 practical improvement tips in the 'tips' array.",
		score.Score, gradeLabel(score.Score),
		score.Correct, score.Total, float64(score.Correct)/float64(max(score.Total, 1))*100,
		score.MissedCount, missedPct,
		score.WrongTimingCount,
		score.ExtraCount, extraPct,
		score.AvgTimingDeviation,
	)

	return
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
