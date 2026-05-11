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
// 토큰 수 최적화: system ~90 토큰, user ~60 토큰 (기존 대비 ~40% 절감)
func BuildFeedbackPrompt(score models.ScoreResult, lang string) (system, user string) {
	lang = NormalizeLang(lang)
	langName := SupportedLangs[lang]

	system = fmt.Sprintf(
		"You are a piano teacher. Respond ONLY in %s (%s). Output valid JSON only.",
		langName, lang,
	)

	user = fmt.Sprintf(
		"Score:%.1f/100 Correct:%d/%d Missed:%d TimingErr:%d Extra:%d AvgDev:%.3fs. Give feedback JSON.",
		score.Score, score.Correct, score.Total,
		score.MissedCount, score.WrongTimingCount,
		score.ExtraCount, score.AvgTimingDeviation,
	)

	return
}
