# flutter_app/ — Flutter 프론트엔드

피아노 연주 평가 결과를 시각화하고, 파일 업로드 및 GPT 피드백을 표시하는 Flutter 앱입니다.  
**Web** + **Android** 동시 지원.

---

## 폴더 구조

```
flutter_app/
├── pubspec.yaml                   # 의존성 정의
├── lib/
│   ├── main.dart                  # 앱 진입점, 탭 셸
│   ├── theme.dart                 # 다크/라이트 테마 토큰
│   ├── models/
│   │   └── record.dart            # ScoreDetail, Feedback, PracticeRecord
│   ├── services/
│   │   └── api_service.dart       # POST /api/analyze, GET /health
│   ├── providers/
│   │   └── record_provider.dart   # ChangeNotifier 상태 관리
│   ├── pages/
│   │   ├── home_page.dart         # 홈 — 점수 추이, 최근 기록
│   │   ├── analysis_page.dart     # 분석 — 파일 업로드, 결과 카드
│   │   ├── history_page.dart      # 기록 — 검색, 목록
│   │   ├── stats_page.dart        # 통계 — 요일별 분포
│   │   └── profile_page.dart      # 프로필 — 이름, 다크모드, 뱃지
│   └── widgets/
│       ├── score_bar.dart         # 점수 바 위젯
│       └── feedback_card.dart     # GPT 피드백 카드 위젯
├── android/
│   └── app/src/main/
│       └── AndroidManifest.xml    # INTERNET + READ_MEDIA_AUDIO 권한
└── web/
    └── index.html                 # Flutter Web 진입점
```

---

## DFD — 데이터 흐름

```
사용자 (앱)
    │
    ├─ WAV 파일 선택 (FilePicker) ──► audioBytes + audioName
    ├─ XML 파일 선택 (FilePicker) ──► sheetBytes + sheetName
    └─ 언어 선택 (ko/en/ja/zh)   ──► lang
    │
    │  "분석 시작하기" 탭
    ▼
RecordProvider.analyze()
    │
    │  ApiService.analyze()
    │  POST /api/analyze (multipart)
    │  ┌─ sheet: bytes
    │  ├─ audio: bytes
    │  └─ lang: string
    │
    ▼
Go 백엔드 (http://localhost:8080)
    │
    │  JSON 응답
    │  { score:{...}, feedback:{...}, grade, lang }
    │
    ▼
PracticeRecord.fromApiResponse()
    │
    ├─► RecordProvider._records.insert(0, record)
    └─► AnalysisPage: _result = record
    │
    ▼
UI 렌더링
    ├─ 점수 + 등급
    ├─ ScoreBar × 3 (음정/누락/박자)
    └─ FeedbackCard (종합/음정/리듬/타이밍/팁/격려)
```

---

## 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `http` | ^1.2.0 | API 호출 (multipart) |
| `file_picker` | ^8.0.0 | WAV/XML 파일 선택 (Web + Android) |
| `provider` | ^6.1.0 | 상태 관리 |
| `shared_preferences` | ^2.2.0 | 로컬 저장소 |
| `fl_chart` | ^0.68.0 | 차트 |
| `intl` | ^0.19.0 | 날짜 포맷 |

---

## 실행 방법

### 사전 요구사항

- Flutter SDK 3.10 이상
- Android Studio / Xcode (Android 빌드용)
- Chrome (Web 실행용)

### 의존성 설치

```bash
cd flutter_app
flutter pub get
```

### Web 실행

```bash
# API 서버 주소 지정 (기본값: http://localhost:8080)
flutter run -d chrome \
  --dart-define=API_BASE=http://localhost:8080
```

### Android 실행

```bash
# 연결된 Android 기기 또는 에뮬레이터
flutter run -d android \
  --dart-define=API_BASE=http://<서버IP>:8080
```

> Android에서는 로컬호스트 대신 PC의 실제 IP 주소를 사용하세요.  
> 예: `--dart-define=API_BASE=http://192.168.1.100:8080`

### Android APK 빌드

```bash
flutter build apk --release \
  --dart-define=API_BASE=http://<서버IP>:8080
# 결과물: build/app/outputs/flutter-apk/app-release.apk
```

### Web 빌드 (정적 파일)

```bash
flutter build web \
  --dart-define=API_BASE=http://localhost:8080
# 결과물: build/web/
```

---

## 환경변수 (dart-define)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `API_BASE` | `http://localhost:8080` | Go 백엔드 API 주소 |

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 파일 선택 안 됨 (Android) | 권한 미부여 | 앱 설정에서 파일 접근 권한 허용 |
| CORS 오류 (Web) | 백엔드 CORS 미설정 | `backend/main.go`의 `corsHandler` 확인 |
| `SocketException` (Android) | HTTP 차단 | `AndroidManifest`의 `usesCleartextTraffic="true"` 확인 |
| 분석 실패 | Go 서버 미실행 | `cd backend && go run main.go` 확인 |
| `Connection refused` | API_BASE 주소 오류 | `--dart-define=API_BASE=...` 확인 |
