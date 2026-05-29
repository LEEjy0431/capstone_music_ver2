# ─────────────────────────────────────────────────────────
# Stage 0: PWA 빌드 (React + Vite)
# ─────────────────────────────────────────────────────────
FROM node:22-alpine AS pwa-builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --silent

COPY index.html vite.config.js ./
COPY public/ ./public/
COPY src/ ./src/

RUN npm run build

# ─────────────────────────────────────────────────────────
# Stage 1: Go 바이너리 빌드
# ─────────────────────────────────────────────────────────
FROM golang:1.24-alpine AS go-builder

WORKDIR /build
COPY backend/go.mod backend/go.sum ./
RUN go mod download

COPY backend/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -o server .

# ─────────────────────────────────────────────────────────
# Stage 2: Python 런타임 + Go 바이너리 + PWA dist
# ─────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

WORKDIR /app

# 시스템 의존성 (librosa, soundfile 등에 필요)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치 (ML 모델 포함 — 최초 빌드 시 수 분 소요)
COPY requirements.txt requirements-llm.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -r requirements-llm.txt

# Go 바이너리 + PWA dist + Python 코드 복사
COPY --from=go-builder /build/server ./server
COPY --from=pwa-builder /app/dist ./dist
COPY code/ ./code/

# 환경변수 기본값
ENV PROJECT_ROOT=/app
ENV PORT=8080
ENV PYTHON_CMD=python3

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD wget -qO- http://localhost:8080/health || exit 1

CMD ["./server"]
