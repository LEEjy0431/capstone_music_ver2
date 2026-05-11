# src/ — React 프론트엔드

피아노 연주 분석 결과를 시각화하고, 파일 업로드 및 GPT 피드백을 표시하는 모바일 퍼스트 React 앱입니다.

---

## 폴더 구조

```
src/
├── main.jsx           # React 앱 진입점
├── App.jsx            # 루트 컴포넌트 — 라우팅, 전역 상태, API 호출
├── HomePage.jsx       # 홈 — 대시보드, 점수 추이, 연습 히트맵
├── AnalysisPage.jsx   # 분석 — 파일 업로드, 언어 선택, 결과 표시
├── HistoryPage.jsx    # 기록 — 연습 세션 목록, 검색
├── StatsPage.jsx      # 통계 — 레이더 차트, 요일별 분포
├── ProfilePage.jsx    # 프로필 — 사용자 정보, 다크모드
├── App.css            # 글로벌 스타일 (최소화)
└── index.css          # 베이스 스타일
```

---

## DFD (Data Flow Diagram)

### Level 1 — 화면·상태 흐름

```
사용자 (Browser)
    │
    │  탭 클릭
    ▼
┌──────────────────────────────────────────────────────────────┐
│  App.jsx  (전역 상태 관리)                                   │
│                                                              │
│  State:                                                      │
│   activeTab  ──────────────────────► 페이지 전환            │
│   records[]  ──────────────────────► 분석 결과 목록         │
│   darkMode   ──────────────────────► 테마 토글              │
│   profile{}  ──────────────────────► 사용자 정보            │
│                                                              │
│  addRecord(sheetFile, audioFile, lang)                       │
│   └─ FormData 생성                                           │
│   └─ fetch POST /api/analyze  ──────────────────────────────┼──► Go 백엔드
│   └─ 응답 → record 객체 생성                                │
│   └─ setRecords(prev => [record, ...prev])                   │
└──────────────────────────────────────────────────────────────┘
    │          │          │          │          │
    ▼          ▼          ▼          ▼          ▼
 HomePage  Analysis  HistoryPage StatsPage ProfilePage
           Page
```

### Level 2 — AnalysisPage 상세 흐름

```
사용자
    │
    ├─ WAV 파일 선택 (FileDropZone)  → audioFile state
    ├─ XML 파일 선택 (FileDropZone)  → sheetFile state
    └─ 언어 선택 (버튼)              → lang state
    │
    │  "분석 시작하기" 클릭
    ▼
handleAnalyze()
    │
    ├─ setAnalyzing(true)
    ├─ onUpload(sheetFile, audioFile, lang)   ← App.jsx의 addRecord
    │       │
    │       │  POST /api/analyze
    │       │  multipart: sheet + audio + lang
    │       ▼
    │  Go 백엔드 응답 대기...
    │       │
    │       ▼
    │  record = {
    │    id, title, date, time,
    │    score, grade, lang,
    │    feedback: { overall, pitch, rhythm,
    │                timing, tips[], encouragement },
    │    scoreDetail: { correct, total, missedCount,
    │                   wrongTimingCount, avgTimingDeviation }
    │  }
    │
    ├─ setResult(record)
    └─ setAnalyzing(false)
    │
    ▼
결과 렌더링
    ├─ 점수 + 등급 표시
    ├─ ScoreBar (정확도 / 놓친 음표 / 박자 오류)
    └─ FeedbackCard (종합 / 음정 / 리듬 / 타이밍 / 팁 / 격려)
```

### Level 3 — 전체 컴포넌트 트리

```
App.jsx
├── [홈]     HomePage
│           ├─ 통계 카드 (총 분석 / 평균 점수 / 연속)
│           ├─ 점수 추이 SVG 그래프
│           └─ 연습 히트맵 (16주 × 7일)
│
├── [분석]  AnalysisPage
│           ├─ FileDropZone  (WAV)
│           ├─ FileDropZone  (XML)
│           ├─ 언어 선택 버튼 (ko / en / ja / zh)
│           ├─ "분석 시작하기" 버튼
│           ├─ 점수 결과 카드
│           │   └─ ScoreBar × 3
│           └─ FeedbackCard
│               ├─ 종합 평가
│               ├─ 음정 / 리듬 / 타이밍
│               ├─ 개선 포인트 (tips[])
│               └─ 격려 메시지
│
├── [기록]  HistoryPage
│           ├─ 검색 입력
│           └─ 세션 목록 (제목 / 날짜 / 점수 / 등급)
│
├── [통계]  StatsPage
│           ├─ 요약 카드 (총 / 평균 / 최고점)
│           ├─ 레이더 차트 (리듬 / 음정 / 다이나믹 / 템포 / 종합)
│           └─ 요일별 연습 분포 막대 그래프
│
└── [프로필] ProfilePage
            ├─ 사용자 정보 편집
            ├─ 다크모드 토글
            └─ 연습 성취 뱃지
```

---

## 환경변수

`.env` 파일 (프로젝트 루트에 생성):

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `VITE_API_BASE` | `http://localhost:8080` | Go 백엔드 API 주소 |

---

## 실행 방법

### 개발 서버

```bash
# 프로젝트 루트에서
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

### 프로덕션 빌드

```bash
npm run build
# dist/ 폴더에 정적 파일 생성
```

---

## 전역 상태 구조 (`App.jsx`)

```javascript
// 분석 결과 레코드
record = {
  id:              number,    // Date.now()
  title:           string,    // 파일명 (확장자 제외)
  date:            string,    // "YYYY-MM-DD"
  time:            string,    // "오후 3:42"
  score:           number,    // 0 ~ 100
  grade:           string,    // "A" | "A-" | "B+" | "B" | "C+" | "C"
  lang:            string,    // "ko" | "en" | "ja" | "zh"
  feedback: {
    overall:       string,
    pitch:         string,
    rhythm:        string,
    timing:        string,
    tips:          string[],
    encouragement: string,
  },
  scoreDetail: {
    correct:              number,
    total:                number,
    missedCount:          number,
    wrongTimingCount:     number,
    avgTimingDeviation:   number,
  },
}
```

---

## 테마 시스템

`App.jsx`의 `getTheme(dark)` 함수가 다크/라이트 색상 토큰을 반환합니다.  
모든 컴포넌트는 `C` prop으로 테마 토큰을 받아 인라인 스타일에 사용합니다.

| 토큰 | 다크 | 라이트 |
|------|------|--------|
| `C.bg` | `#111111` | `#f5f5f5` |
| `C.surface` | `#1c1c1c` | `#ffffff` |
| `C.gold` | `#F0B429` | `#d4900a` |
| `C.textPrimary` | `#f0f0f0` | `#111111` |
| `C.textSecondary` | `#888888` | `#555555` |

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 분석 버튼 비활성화 | WAV 또는 XML 파일 미선택 | 두 파일 모두 업로드 |
| `서버 오류` 메시지 | Go 백엔드 미실행 | `cd backend && go run main.go` 실행 확인 |
| CORS 오류 | API 주소 불일치 | `.env`의 `VITE_API_BASE` 와 Go 서버 포트 일치 확인 |
| 점수가 `NaN` 으로 표시 | API 응답 구조 불일치 | Go 백엔드 버전 최신 여부 확인 (`git pull`) |
