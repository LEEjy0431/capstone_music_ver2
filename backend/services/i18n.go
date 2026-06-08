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

// langInstruction은 소형 모델(Qwen 등)을 위한 강제 언어 지시어다.
var langInstruction = map[string]string{
	"ko": "반드시 한국어로만 작성하세요. 영어를 절대 사용하지 마세요. All output must be in Korean (한국어).",
	"en": "Respond in English only.",
	"ja": "必ず日本語のみで回答してください。英語は使用しないでください。",
	"zh": "必须只用中文回答。不要使用英文。",
}

// gradeLabel은 점수를 언어별 등급 문자열로 변환한다.
func gradeLabel(score float64, lang string) string {
	if lang == "ko" {
		switch {
		case score >= 95:
			return "S (완벽)"
		case score >= 90:
			return "A+ (매우 우수)"
		case score >= 85:
			return "A (우수)"
		case score >= 80:
			return "B+ (양호)"
		case score >= 75:
			return "B (보통)"
		case score >= 70:
			return "C+ (노력 필요)"
		default:
			return "C (많은 연습 필요)"
		}
	}
	switch {
	case score >= 95:
		return "S (perfect)"
	case score >= 90:
		return "A+ (excellent)"
	case score >= 85:
		return "A (great)"
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

// BuildFeedbackPrompt는 채점 결과와 언어 코드를 받아 system/user 프롬프트를 생성한다.
// Qwen 같은 소형 모델도 한국어로 응답하도록 프롬프트를 언어별로 최적화한다.
func BuildFeedbackPrompt(score models.ScoreResult, lang string) (system, user string) {
	lang = NormalizeLang(lang)
	langName := SupportedLangs[lang]
	forceInstr := langInstruction[lang]

	system = fmt.Sprintf(
		"You are an expert piano teacher. %s\n"+
			"Output ONLY a raw JSON object — no markdown, no explanation, no extra text.\n"+
			"Required JSON keys (all string values must be in %s):\n"+
			`  "overall": 2-3문장 종합 평가`+"\n"+
			`  "pitch": 음정 정확도 피드백`+"\n"+
			`  "rhythm": 리듬/박자 피드백`+"\n"+
			`  "timing": 타이밍 피드백`+"\n"+
			`  "tips": 2-3개 개선 팁 배열`+"\n"+
			`  "encouragement": 격려 한 문장`,
		forceInstr, langName,
	)

	missedPct := 0.0
	extraPct := 0.0
	if score.Total > 0 {
		missedPct = float64(score.MissedCount) / float64(score.Total) * 100
		extraPct = float64(score.ExtraCount) / float64(score.Total) * 100
	}
	correctPct := 0.0
	if score.Total > 0 {
		correctPct = float64(score.Correct) / float64(score.Total) * 100
	}

	if lang == "ko" {
		user = fmt.Sprintf(
			"피아노 연주 분석 결과:\n"+
				"- 최종 점수: %.1f점 / 100점 (등급: %s)\n"+
				"- 정확한 음표: %d개 / %d개 (%.1f%%)\n"+
				"- 누락된 음표: %d개 (%.1f%%)\n"+
				"- 박자 오류: %d개\n"+
				"- 여분의 음표: %d개 (%.1f%%)\n"+
				"- 평균 타이밍 오차: %.3f초\n\n"+
				"위 데이터를 바탕으로 한국어로 피드백 JSON을 작성하세요. 반드시 한국어로만 답하세요.",
			score.Score, gradeLabel(score.Score, lang),
			score.Correct, score.Total, correctPct,
			score.MissedCount, missedPct,
			score.WrongTimingCount,
			score.ExtraCount, extraPct,
			score.AvgTimingDeviation,
		)
	} else {
		user = fmt.Sprintf(
			"Piano performance analysis result:\n"+
				"- Overall score: %.1f/100 (Grade: %s)\n"+
				"- Correct notes: %d / %d (%.1f%%)\n"+
				"- Missed notes: %d (%.1f%%)\n"+
				"- Timing errors: %d\n"+
				"- Extra notes: %d (%.1f%%)\n"+
				"- Avg timing deviation: %.3fs\n\n"+
				"Write feedback JSON in %s only.",
			score.Score, gradeLabel(score.Score, lang),
			score.Correct, score.Total, correctPct,
			score.MissedCount, missedPct,
			score.WrongTimingCount,
			score.ExtraCount, extraPct,
			score.AvgTimingDeviation,
			langName,
		)
	}

	return
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
