package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"

	"github.com/joho/godotenv"

	"capstone/backend/handlers"
)

func loadEnv() {
	// PROJECT_ROOT/.env 우선, 없으면 현재 디렉터리 및 상위 디렉터리 시도
	if root := os.Getenv("PROJECT_ROOT"); root != "" {
		if err := godotenv.Load(filepath.Join(root, ".env")); err == nil {
			log.Printf(".env 로딩: %s/.env", root)
			return
		}
	}
	// go run 위치 기준 탐색 (backend/ 또는 프로젝트 루트)
	for _, p := range []string{".env", "../.env"} {
		if err := godotenv.Load(p); err == nil {
			abs, _ := filepath.Abs(p)
			log.Printf(".env 로딩: %s", abs)
			return
		}
	}
	log.Println("경고: .env 파일을 찾지 못했습니다. 시스템 환경변수를 사용합니다.")
}

func corsHandler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func main() {
	loadEnv()

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/api/analyze", handlers.AnalyzeHandler)
	mux.HandleFunc("/api/feedback/stream", handlers.FeedbackStreamHandler)
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintln(w, `{"status":"ok"}`)
	})

	// PWA 정적 파일 서빙 (dist/ 폴더가 있을 때만 활성화)
	root := os.Getenv("PROJECT_ROOT")
	if root == "" {
		if exe, err := os.Executable(); err == nil {
			root = filepath.Dir(filepath.Dir(exe))
		}
	}
	distDir := filepath.Join(root, "dist")
	if info, err := os.Stat(distDir); err == nil && info.IsDir() {
		mux.Handle("/", handlers.SPAHandler(distDir))
		log.Printf("PWA 서빙: %s → http://localhost%s", distDir, ":"+port)
	} else {
		log.Println("dist/ 없음 — PWA 서빙 비활성화 (npm run build 후 재시작)")
	}

	addr := ":" + port
	log.Printf("서버 시작: http://localhost%s", addr)
	log.Fatal(http.ListenAndServe(addr, corsHandler(mux)))
}
