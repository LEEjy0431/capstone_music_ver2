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
# Stage 2: Python 런타임 + Go 바이너리
#
# TensorFlow/torch 의존성으로 이미지 크기가 크므로
# 개발 환경에서는 --target go-builder 로 빌드 후
# 로컬 Python을 사용하는 방식도 가능.
# ─────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

WORKDIR /app

# 시스템 의존성 (librosa, soundfile 등에 필요)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치 (ML 모델 포함 — 빌드 시 수 분 소요)
COPY requirements.txt requirements-llm.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -r requirements-llm.txt

# Go 바이너리 복사
COPY --from=go-builder /build/server ./server

# Python 파이프라인 코드 복사
COPY code/ ./code/

# 환경변수 기본값
ENV PROJECT_ROOT=/app
ENV PORT=8080
ENV PYTHON_CMD=python3

EXPOSE 8080

CMD ["./server"]
