package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	"capstone/backend/handlers"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/api/analyze", handlers.AnalyzeHandler)
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintln(w, `{"status":"ok"}`)
	})

	addr := ":" + port
	log.Printf("서버 시작: http://localhost%s", addr)
	log.Fatal(http.ListenAndServe(addr, mux))
}
