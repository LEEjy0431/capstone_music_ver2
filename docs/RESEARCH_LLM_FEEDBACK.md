# LLM 피드백 출력 연구 — 속도 및 구조화 개선

> 현황 분석 → 3가지 개선 방향 → 선택 기준 → 프로토타입 구현 경로

---

## 1. 현재 구조의 병목

```
[분석 요청]
    │
    ▼  ~10~30s (Python 파이프라인)
Python 채점 완료
    │
    ▼  +3~8s (GPT blocking 호출)
gpt-4o-mini 응답 전체 대기
    │
    ▼  응답 한 번에 클라이언트 전달
Flutter UI 표시
```

### 실제 지연 원인

| 단계 | 소요 시간 | 원인 |
|------|-----------|------|
| Python 파이프라인 | 10~30초 | piano_transcription 모델 추론 |
| GPT API 첫 토큰 | 0.5~1.5초 | Cold start, 네트워크 |
| GPT 전체 완료 | +2~6초 | ~300 토큰 생성 대기 |
| 체감 지연 | **최대 40초** | 완료 전까지 UI 변화 없음 |

**핵심 문제**: GPT가 마지막 토큰까지 생성 완료될 때까지 사용자는 빈 화면을 본다.  
Python 파이프라인이 끝나고도 추가로 3~8초를 기다려야 한다.

---

## 2. 개선 방향 3가지 비교

### 방향 A — SSE 스트리밍

GPT가 토큰을 생성하는 즉시 클라이언트로 전달.

```
Python 완료 → GPT 스트림 시작
                │
                ├─ 0.5s: "전반적으로..."    → 화면 즉시 표시 시작
                ├─ 1.0s: "음정은..."
                ├─ 2.0s: "리듬 오류..."
                └─ 3.5s: 완료 (done 이벤트)
```

| 항목 | 평가 |
|------|------|
| 체감 속도 개선 | ★★★★★ 첫 텍스트가 0.5초 내 표시 |
| 구현 복잡도 | ★★★☆☆ SSE 파싱, 스트림 재조립 필요 |
| JSON 구조 보장 | ★★☆☆☆ 스트리밍 중 파싱 불가 |
| Flutter 구현 | SSE 수신 후 done 이벤트에서 JSON 파싱 |

---

### 방향 B — 구조화 출력 최적화

`response_format: json_object` → JSON Schema 강제 + 프롬프트 토큰 최소화.

```
현재 프롬프트: ~350 토큰 → 최적화 후: ~180 토큰
응답 토큰:    ~280 토큰 → max_tokens 제한: 250 토큰
Temperature:  0.7       → 0.3 (JSON 안정성)
```

| 항목 | 평가 |
|------|------|
| 체감 속도 개선 | ★★★☆☆ 전체 시간 ~35% 단축 |
| 구현 복잡도 | ★★☆☆☆ 프롬프트 수정 + 파라미터 조정 |
| JSON 구조 보장 | ★★★★★ 스키마 강제로 필드 누락 없음 |
| 안정성 | ★★★★★ JSON 파싱 실패율 대폭 감소 |

---

### 방향 C — 병렬 섹션 분리 생성

피드백을 3개 그룹으로 나눠 동시에 GPT 호출.

```
Go goroutine 3개 동시 실행:
  ├─ GPT 호출 1: overall (50 토큰)      → 1.2s
  ├─ GPT 호출 2: pitch+rhythm+timing    → 1.5s
  └─ GPT 호출 3: tips+encouragement     → 1.0s
병렬 완료 후 합산: 최대 1.5s (직렬 3~6s 대비)
```

| 항목 | 평가 |
|------|------|
| 체감 속도 개선 | ★★★★☆ 전체 시간 ~60% 단축 |
| 구현 복잡도 | ★★★★☆ goroutine 동기화, 3배 API 호출 |
| API 비용 | ★★☆☆☆ 호출 횟수 3배 |
| JSON 구조 보장 | ★★★★☆ 각 섹션 분리 스키마 |

---

## 3. 선택 기준 매트릭스

```
                    구조 안정성
                        ↑
                        │     [B] JSON Schema
                        │      + 토큰 최적화
                        │
             [C] 병렬   │
               분리     │
                        │
────────────────────────┼────────────────→ 체감 속도
                        │
                        │   [A] SSE
                        │   스트리밍
                        │
```

### 권장 조합

> **방향 A + B 동시 적용** (이 프로토타입이 구현하는 방식)

1. **방향 B (구조화 최적화)**: 먼저 적용. 프롬프트 토큰 감소 + JSON Schema 강제
2. **방향 A (SSE 스트리밍)**: 추가 적용. 체감 속도 최우선 개선
3. **방향 C (병렬)**: API 비용 여유 생기면 추가 고려

---

## 4. 구현 계획

### 4-1. 프롬프트 최적화 (방향 B)

**변경 전** (현재 `i18n.go`):
```go
// system prompt: ~180 토큰
// user prompt: ~120 토큰
// temperature: 0.7
// max_tokens: 없음 (기본값 4096)
```

**변경 후** (`i18n.go` + `gpt.go` 수정):
```go
// system prompt: ~90 토큰 (역할+언어+스키마만)
// user prompt: ~60 토큰 (수치만, 설명 제거)
// temperature: 0.3
// max_tokens: 400
```

### 4-2. SSE 스트리밍 엔드포인트 (방향 A)

**신규**: `GET /api/feedback/stream?score=...&lang=ko`

```
클라이언트 ←── SSE ──── Go 서버 ←── stream ──── OpenAI
               │
               ├── event: chunk  data: {"text":"전반적으로..."}
               ├── event: chunk  data: {"text":"음정은 83%..."}
               ├── event: chunk  data: {"text":"리듬 오류..."}
               └── event: done   data: {"feedback":{...전체 JSON...}}
```

**파일 구조**:
```
backend/services/
├── gpt.go            ← 기존 blocking 방식 (유지)
├── gpt_stream.go     ← 신규: SSE 스트리밍 서비스
├── i18n.go           ← 프롬프트 최적화 (수정)
└── i18n_schema.go    ← 신규: JSON Schema 정의
backend/handlers/
├── analyze.go        ← 기존 (유지)
└── feedback_stream.go ← 신규: /api/feedback/stream 핸들러
```

### 4-3. Flutter SSE 수신 (방향 A)

```dart
// lib/services/api_service.dart 확장
static Stream<FeedbackEvent> feedbackStream({
  required ScoreDetail score,
  required String lang,
}) async* {
  final client = http.Client();
  final request = http.Request('GET', uri);
  final response = await client.send(request);
  
  await for (final chunk in response.stream.transform(utf8.decoder)) {
    // "data: {...}\n\n" 파싱
    // FeedbackEvent(type, text, feedback) yield
  }
}
```

---

## 5. 성능 예측

| 지표 | 현재 | 최적화 후 (A+B) |
|------|------|----------------|
| 첫 글자 표시 | ~35초 (분석+GPT 완료 후) | ~12초 (분석 완료 후 0.5s) |
| 피드백 완료 | ~38초 | ~16초 |
| JSON 파싱 실패율 | ~2~5% | ~0.1% (스키마 강제) |
| GPT 토큰 비용 | ~600 토큰/요청 | ~400 토큰/요청 |

---

## 6. 참고 — OpenAI 스트리밍 응답 형식

```
POST /v1/chat/completions
{ "stream": true, ... }

응답 (chunked):
data: {"choices":[{"delta":{"content":"전"},"finish_reason":null}]}
data: {"choices":[{"delta":{"content":"반"},"finish_reason":null}]}
...
data: {"choices":[{"delta":{},"finish_reason":"stop"}]}
data: [DONE]
```

Go에서 처리:
```go
scanner := bufio.NewScanner(resp.Body)
for scanner.Scan() {
    line := scanner.Text()
    if !strings.HasPrefix(line, "data: ") { continue }
    payload := strings.TrimPrefix(line, "data: ")
    if payload == "[DONE]" { break }
    // json.Unmarshal([]byte(payload), &chunk)
    // w.(http.Flusher).Flush()
}
```
