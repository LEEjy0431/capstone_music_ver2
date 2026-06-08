package services

import (
	"fmt"
	"sort"
	"strings"

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
		"NEVER use Chinese characters. Korean Hangul only.",
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
		case score >= 70:
			return "B (보통)"
		case score >= 55:
			return "C+ (노력 필요)"
		case score >= 40:
			return "C (미흡)"
		default:
			return "F (많은 연습 필요)"
		}
	}
	switch {
	case score >= 95:
		return "S (perfect)"
	case score >= 85:
		return "A (great)"
	case score >= 70:
		return "B (average)"
	case score >= 55:
		return "C (needs work)"
	default:
		return "F (needs significant improvement)"
	}
}

// scoreTone은 점수에 따라 피드백 톤 지시어와 few-shot 예시를 반환한다.
func scoreTone(score float64) (toneInstruction, example string) {
	switch {
	case score >= 85:
		toneInstruction = "점수가 높습니다. 긍정적이고 격려하는 톤으로 작성하되, 더 발전할 수 있는 부분도 언급하세요."
		example = `{"overall":"연주가 전반적으로 매우 훌륭합니다. 정확한 음정과 안정된 박자가 인상적입니다.",` +
			`"pitch":"음정 정확도가 매우 높습니다. 표현력을 더 높이면 완벽해질 것입니다.",` +
			`"rhythm":"박자가 안정적이고 리듬감이 좋습니다.",` +
			`"timing":"타이밍이 정확합니다. 빠른 구간에서도 흔들림이 없습니다.",` +
			`"tips":["다양한 다이나믹 표현을 연습해보세요.","감정 표현을 더 풍부하게 해보세요."],` +
			`"encouragement":"훌륭한 연주입니다. 이 수준을 유지하면서 더욱 발전하세요!"}`

	case score >= 65:
		toneInstruction = "점수가 평균 수준입니다. 잘된 부분은 칭찬하고, 부족한 부분은 구체적으로 지적하세요. 솔직하게 개선이 필요하다고 말하세요."
		example = `{"overall":"전반적으로 보통 수준의 연주입니다. 일부 음표는 정확했지만 누락된 음표가 많아 개선이 필요합니다.",` +
			`"pitch":"음정 정확도가 부분적으로 좋지만, 일부 구간에서 음을 놓쳤습니다.",` +
			`"rhythm":"리듬이 불안정한 구간이 있습니다. 박자 연습이 필요합니다.",` +
			`"timing":"타이밍 오차가 다소 있습니다. 느린 템포부터 연습하는 것이 좋겠습니다.",` +
			`"tips":["메트로놈과 함께 느린 속도로 연습하세요.","어려운 구간을 반복 연습하세요."],` +
			`"encouragement":"꾸준히 연습하면 반드시 실력이 향상될 것입니다."}`

	case score >= 40:
		toneInstruction = "점수가 낮습니다. 부족한 점을 명확하고 직접적으로 지적하세요. 칭찬보다 개선 방향에 집중하세요."
		example = `{"overall":"연주에 많은 부분이 부족합니다. 정확한 음표 수가 매우 적고 누락된 음표가 많습니다. 기초부터 다시 연습이 필요합니다.",` +
			`"pitch":"음정 정확도가 낮습니다. 악보를 정확히 읽고 각 음을 정확히 연주하는 연습이 필요합니다.",` +
			`"rhythm":"리듬이 전반적으로 불안정합니다. 박자 감각을 기르는 것이 우선입니다.",` +
			`"timing":"타이밍 오차가 큽니다. 메트로놈을 사용하여 정확한 박자 감각을 키우세요.",` +
			`"tips":["악보를 먼저 충분히 읽고 음을 익힌 후 연주하세요.","매우 느린 속도로 정확하게 연습하세요.","메트로놈을 항상 사용하세요."],` +
			`"encouragement":"지금은 힘들더라도 꾸준히 연습하면 반드시 나아질 것입니다."}`

	default: // score < 40
		toneInstruction = "점수가 매우 낮습니다. 대부분의 음표를 놓쳤거나 틀렸습니다. 솔직하게 많이 틀렸다고 말하고, 기초부터 다시 시작해야 한다고 명확히 알려주세요. 거짓 칭찬은 하지 마세요."
		example = `{"overall":"연주 점수가 매우 낮습니다. 대부분의 음표를 놓쳤으며, 악보와 다른 음원을 사용했거나 기초 연습이 많이 부족한 상태입니다. 기초부터 다시 시작해야 합니다.",` +
			`"pitch":"정확히 연주된 음표가 매우 적습니다. 악보의 음표를 하나씩 정확히 익히는 것부터 시작하세요.",` +
			`"rhythm":"리듬과 박자가 전혀 맞지 않습니다. 박자 연습을 최우선으로 해야 합니다.",` +
			`"timing":"타이밍 오차가 심각합니다. 악보와 연주 음원이 일치하는지 먼저 확인하세요.",` +
			`"tips":["올바른 악보와 음원을 사용하고 있는지 확인하세요.","한 마디씩 아주 천천히 연습하세요.","기초 음계 연습부터 다시 시작하세요."],` +
			`"encouragement":"지금은 많이 부족하지만, 기초부터 차근차근 연습하면 반드시 나아질 것입니다."}`
	}
	return
}

// BuildFeedbackPrompt는 채점 결과와 언어 코드를 받아 system/user 프롬프트를 생성한다.
// 점수 구간별 톤과 few-shot 예시를 포함해 정확한 평가를 유도한다.
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
		toneInstr, example := scoreTone(score.Score)
		missedDetail := formatMissedNotes(score.MissedNotesDetail)

		system = fmt.Sprintf(
			"당신은 전문 피아노 선생님입니다. 학생의 연주 분석 결과를 보고 솔직하고 정확한 피드백을 작성합니다.\n"+
				"반드시 순수 한국어(한글)로만 답하세요. 영어, 한자, 중국어를 절대 사용하지 마세요.\n\n"+
				"[톤 지침] %s\n\n"+
				"아래 JSON 형식으로만 답하세요. 다른 텍스트는 절대 쓰지 마세요.\n"+
				"출력 예시:\n%s",
			toneInstr, example,
		)

		user = fmt.Sprintf(
			"피아노 연주 분석 결과:\n"+
				"- 점수: %.1f점 / 100점 (등급: %s)\n"+
				"- 정확한 음표: %d개 / %d개 (%.1f%%)\n"+
				"- 누락된 음표: %d개 (%.1f%%)\n"+
				"- 박자 오류: %d개\n"+
				"- 여분의 음표: %d개 (%.1f%%)\n"+
				"- 평균 타이밍 오차: %.3f초\n"+
				"- BPM: %.0f\n\n"+
				"[마디별 누락 음표]\n%s\n\n"+
				"위 결과를 바탕으로 실제 점수에 맞는 솔직한 한국어 피드백 JSON을 작성하세요.\n"+
				"'overall'에는 몇 마디에서 어떤 음이 틀렸는지 구체적으로 언급하세요.",
			score.Score, gradeLabel(score.Score, lang),
			score.Correct, score.Total, correctPct,
			score.MissedCount, missedPct,
			score.WrongTimingCount,
			score.ExtraCount, extraPct,
			score.AvgTimingDeviation,
			score.BPM,
			missedDetail,
		)
	} else {
		forceInstr := langInstruction[lang]
		var toneLine string
		switch {
		case score.Score >= 85:
			toneLine = "The score is high. Be positive and encouraging."
		case score.Score >= 65:
			toneLine = "The score is average. Be honest about strengths and weaknesses."
		case score.Score >= 40:
			toneLine = "The score is low. Be direct about what needs improvement. Don't over-praise."
		default:
			toneLine = "The score is very low. Most notes were missed or wrong. Be honest and clear. Do NOT give false praise."
		}

		system = fmt.Sprintf(
			"You are an expert piano teacher. %s\n%s\n"+
				"Output ONLY a raw JSON object. No markdown, no extra text.\n"+
				`Keys: "overall", "pitch", "rhythm", "timing", "tips" (array 2-3), "encouragement". All values in %s.`,
			forceInstr, toneLine, langName,
		)
		user = fmt.Sprintf(
			"Piano performance:\n"+
				"- Score: %.1f/100 (Grade: %s)\n"+
				"- Correct: %d/%d (%.1f%%)\n"+
				"- Missed: %d (%.1f%%)\n"+
				"- Timing errors: %d\n"+
				"- Extra: %d (%.1f%%)\n"+
				"- Avg deviation: %.3fs\n\n"+
				"Write honest feedback JSON in %s.",
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

// formatMissedNotes는 누락 음표를 마디별로 그룹화해 읽기 쉬운 문자열로 변환한다.
// 예: "마디 1: C4, E4 / 마디 3: G4 / 마디 5: D4, F#3"
func formatMissedNotes(notes []models.NoteDetail) string {
	if len(notes) == 0 {
		return "없음"
	}

	// 마디별 음표 그룹화
	byMeasure := make(map[int][]string)
	for _, n := range notes {
		m := n.Measure
		if m < 1 {
			m = 1
		}
		byMeasure[m] = append(byMeasure[m], n.Note)
	}

	// 마디 번호 정렬
	measures := make([]int, 0, len(byMeasure))
	for m := range byMeasure {
		measures = append(measures, m)
	}
	sort.Ints(measures)

	parts := make([]string, 0, len(measures))
	for _, m := range measures {
		noteList := strings.Join(byMeasure[m], ", ")
		parts = append(parts, fmt.Sprintf("마디 %d: %s", m, noteList))
	}

	result := strings.Join(parts, " / ")
	if len(result) > 400 { // 너무 길면 잘라냄
		result = result[:397] + "..."
	}
	return result
}
