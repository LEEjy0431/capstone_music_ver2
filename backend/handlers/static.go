package handlers

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

// SPAHandler는 distDir 내 정적 파일을 서빙하고,
// 존재하지 않는 경로는 index.html로 폴백한다 (SPA 라우팅 지원).
func SPAHandler(distDir string) http.Handler {
	fs := http.FileServer(http.Dir(distDir))

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// /api/* 와 /health 는 이 핸들러에 도달하지 않지만 방어적으로 체크
		if strings.HasPrefix(r.URL.Path, "/api/") || r.URL.Path == "/health" {
			http.NotFound(w, r)
			return
		}

		target := filepath.Join(distDir, filepath.Clean("/"+r.URL.Path))
		if _, err := os.Stat(target); os.IsNotExist(err) {
			// SPA 폴백 — React Router 경로를 index.html로 처리
			http.ServeFile(w, r, filepath.Join(distDir, "index.html"))
			return
		}
		fs.ServeHTTP(w, r)
	})
}
