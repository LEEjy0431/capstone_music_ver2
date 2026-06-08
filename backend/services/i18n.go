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
	"ko": "반드시 한국어(한글)로만 작성하세요. " +
		"한자(漢字), 중국어, 일본어 문자를 절대 사용하지 마세요. " +
		"오직 한글, 숫자, 기본 문장부호(.,!?…)만 사용하세요. " +
		"NEVER use Chinese characters (漢字/汉字). Korean Hangul only.",
	"en": "Respond in English only. No Chinese or Japanese characters.",
	"ja": "必ず日本語のみで回答してください。中国語の漢字は使用しないでください。",
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
// 한국어는 few-shot 예시를 포함해 소형 모델(Qwen)도 한글로 응답하도록 강제한다.
func BuildFeedbackPrompt(score models.ScoreResult, lang string) (system, user string) {
	lang = NormalizeLang(lang)
	langName := SupportedLangs[lang]

	missedPct := 0.0
	extraPct := 0.0
	correctPct := 0.0
	if score.Total > 0 {
		missedPct = float64(score.MissedCount) / float64(score.Total) * 100
		extraPct = float64(score.ExtraCount) / float64(score.Total) * 100
		correctPct = float64(score.Correct) / float64(score.Total) * 100
	}

	if lang == "ko" {
		// 한국어: few-shot 예시 포함, 전체 프롬프트를 한국어로 작성
		system = "당신은 전문 피아노 선생님입니다. 학생의 연주 분석 결과를 보고 피드백을 작성합니다.\n" +
			"반드시 순수 한국어(한글)로만 답하세요. 영어, 한자, 중국어를 절대 사용하지 마세요.\n" +
			"아래 JSON 형식으로만 답하세요. 다른 텍스트는 절대 쓰지 마세요.\n\n" +
			"출력 예시:\n" +
			`{"overall":"연주가 전반적으로 매우 훌륭합니다. 정확한 음정과 안정된 박자가 인상적입니다.",` +
			`"pitch":"음정 정확도가 높습니다. 조금 더 세밀한 표현을 연습해보세요.",` +
			`"rhythm":"박자가 안정적입니다. 다음 단계로 리듬 변화를 시도해보세요.",` +
			`"timing":"타이밍이 대체로 좋습니다. 빠른 구간에서 조금 더 주의가 필요합니다.",` +
			`"tips":["매일 30분씩 스케일 연습을 하세요.","느린 템포로 정확하게 연습하세요."],` +
			`"encouragement":"정말 잘 하고 있습니다. 계속 연습하면 더욱 발전할 것입니다."}`

		user = fmt.Sprintf(
			"피아노 연주 분석 결과:\n"+
				"- 점수: %.1f점 / 100점 (등급: %s)\n"+
				"- 정확한 음표: %d개 / %d개 (%.1f%%)\n"+
				"- 누락된 음표: %d개 (%.1f%%)\n"+
				"- 박자 오류: %d개\n"+
				"- 여분의 음표: %d개 (%.1f%%)\n"+
				"- 평균 타이밍 오차: %.3f초\n\n"+
				"위 결과를 바탕으로 한국어 피드백 JSON을 작성하세요.",
			score.Score, gradeLabel(score.Score, lang),
			score.Correct, score.Total, correctPct,
			score.MissedCount, missedPct,
			score.WrongTimingCount,
			score.ExtraCount, extraPct,
			score.AvgTimingDeviation,
		)
	} else {
		forceInstr := langInstruction[lang]
		system = fmt.Sprintf(
			"You are an expert piano teacher. %s\n"+
				"Output ONLY a raw JSON object. No markdown, no extra text.\n"+
				`Keys: "overall", "pitch", "rhythm", "timing", "tips" (array 2-3), "encouragement". All values in %s.`,
			forceInstr, langName,
		)
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
