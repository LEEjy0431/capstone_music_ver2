package services

import (
	"sync"
	"time"

	"capstone/backend/models"
)

type scoreEntry struct {
	score     models.ScoreResult
	expiresAt time.Time
}

var scoreStore sync.Map

const scoreTTL = 5 * time.Minute

// StoreScore는 채점 결과를 sessionID 키로 5분간 메모리에 저장한다.
func StoreScore(sessionID string, score models.ScoreResult) {
	scoreStore.Store(sessionID, scoreEntry{
		score:     score,
		expiresAt: time.Now().Add(scoreTTL),
	})
}

// GetScore는 sessionID에 해당하는 채점 결과를 반환한다.
// 만료되었거나 존재하지 않으면 false를 반환한다.
func GetScore(sessionID string) (models.ScoreResult, bool) {
	val, ok := scoreStore.Load(sessionID)
	if !ok {
		return models.ScoreResult{}, false
	}
	entry := val.(scoreEntry)
	if time.Now().After(entry.expiresAt) {
		scoreStore.Delete(sessionID)
		return models.ScoreResult{}, false
	}
	return entry.score, true
}
