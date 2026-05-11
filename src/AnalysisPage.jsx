import { useState, useRef } from "react";

const LANG_OPTIONS = [
  { code: "ko", label: "한국어" },
  { code: "en", label: "English" },
  { code: "ja", label: "日本語" },
  { code: "zh", label: "中文" },
];

function FileDropZone({ C, label, accept, hint, file, onFile }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) onFile(f);
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current.click()}
      style={{
        border: `2px dashed ${dragging ? C.gold : file ? C.goldDark : "#3a3a3a"}`,
        borderRadius: 14, padding: "24px 18px",
        display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
        cursor: "pointer", background: dragging ? "rgba(240,180,41,0.05)" : C.surface,
        transition: "all .2s",
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: C.textSecondary }}>{label}</div>
      {file ? (
        <>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.gold, wordBreak: "break-all", textAlign: "center" }}>{file.name}</div>
          <div style={{ fontSize: 12, color: C.textMuted }}>{(file.size / 1024 / 1024).toFixed(2)} MB</div>
        </>
      ) : (
        <>
          <div style={{ fontSize: 13, color: C.textMuted }}>{hint}</div>
          <div style={{ background: C.gold, color: C.goldText, borderRadius: 8, padding: "6px 16px", fontSize: 12, fontWeight: 700, marginTop: 4 }}>
            파일 선택
          </div>
        </>
      )}
      <input ref={inputRef} type="file" accept={accept} style={{ display: "none" }} onChange={(e) => e.target.files[0] && onFile(e.target.files[0])} />
    </div>
  );
}

function ScoreBar({ C, label, value, color }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 13, color: C.textSecondary }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 700, color }}>{value}</span>
      </div>
      <div style={{ height: 6, background: "#2a2a2a", borderRadius: 3 }}>
        <div style={{ height: "100%", width: `${Math.min(value, 100)}%`, background: color, borderRadius: 3, transition: "width 1s ease" }} />
      </div>
    </div>
  );
}

function FeedbackCard({ C, feedback }) {
  return (
    <div style={{ background: C.cardBg, borderRadius: 14, padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ fontSize: 15, fontWeight: 700, color: C.textPrimary }}>GPT 피드백</div>

      {[
        { label: "종합 평가", text: feedback.overall, color: C.gold },
        { label: "음정", text: feedback.pitch, color: "#80d0ff" },
        { label: "리듬", text: feedback.rhythm, color: "#7ee8a2" },
        { label: "타이밍", text: feedback.timing, color: "#c77dff" },
      ].map((item) => (
        <div key={item.label}>
          <div style={{ fontSize: 12, fontWeight: 700, color: item.color, marginBottom: 4 }}>{item.label}</div>
          <div style={{ fontSize: 13, color: C.textSecondary, lineHeight: 1.6 }}>{item.text}</div>
        </div>
      ))}

      {feedback.tips?.length > 0 && (
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#ff9f43", marginBottom: 8 }}>개선 포인트</div>
          {feedback.tips.map((tip, i) => (
            <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6 }}>
              <span style={{ color: "#ff9f43", fontWeight: 700, flexShrink: 0 }}>{i + 1}.</span>
              <span style={{ fontSize: 13, color: C.textSecondary, lineHeight: 1.5 }}>{tip}</span>
            </div>
          ))}
        </div>
      )}

      {feedback.encouragement && (
        <div style={{ background: "rgba(240,180,41,0.1)", borderRadius: 10, padding: "12px 14px", fontSize: 13, color: C.gold, fontStyle: "italic", lineHeight: 1.6 }}>
          {feedback.encouragement}
        </div>
      )}
    </div>
  );
}

export default function AnalysisPage({ C, onNavigate, onUpload }) {
  const [audioFile, setAudioFile] = useState(null);
  const [sheetFile, setSheetFile] = useState(null);
  const [lang, setLang] = useState("ko");
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const scoreColor = (v) => v >= 90 ? "#80d0ff" : v >= 80 ? C.gold : "#ff9f43";

  async function handleAnalyze() {
    if (!audioFile || !sheetFile) return;
    setAnalyzing(true);
    setError(null);
    try {
      const r = await onUpload(sheetFile, audioFile, lang);
      setResult(r);
    } catch (e) {
      setError(e.message || "분석 중 오류가 발생했습니다.");
    } finally {
      setAnalyzing(false);
    }
  }

  function handleReset() {
    setAudioFile(null);
    setSheetFile(null);
    setResult(null);
    setError(null);
  }

  const canAnalyze = audioFile && sheetFile && !analyzing;

  return (
    <div style={{ padding: "56px 18px 110px", display: "flex", flexDirection: "column", gap: 16 }}>
      <div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: C.textPrimary, margin: 0, letterSpacing: "-.02em" }}>연습 분석</h1>
        <p style={{ fontSize: 14, color: C.textSecondary, margin: "6px 0 0" }}>악보와 음원을 업로드하여 AI 피드백을 받으세요</p>
      </div>

      {!result && (
        <>
          <FileDropZone
            C={C} label="연주 음원 파일 (WAV)" accept=".wav,audio/*"
            hint="WAV 파일을 드래그하거나 클릭하세요"
            file={audioFile} onFile={setAudioFile}
          />
          <FileDropZone
            C={C} label="악보 파일 (MusicXML)" accept=".xml,.mxl"
            hint="MusicXML 파일을 드래그하거나 클릭하세요"
            file={sheetFile} onFile={setSheetFile}
          />

          <div style={{ background: C.surface, borderRadius: 14, padding: "14px 16px" }}>
            <div style={{ fontSize: 13, color: C.textSecondary, marginBottom: 10, fontWeight: 600 }}>피드백 언어</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {LANG_OPTIONS.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLang(l.code)}
                  style={{
                    padding: "8px 16px", borderRadius: 20, border: "none", fontSize: 13, fontWeight: 600,
                    cursor: "pointer", transition: ".2s",
                    background: lang === l.code ? C.gold : C.cardBg,
                    color: lang === l.code ? C.goldText : C.textSecondary,
                  }}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={!canAnalyze}
            style={{
              width: "100%",
              background: canAnalyze ? `linear-gradient(135deg,${C.gold},${C.goldDark})` : "#2a2a2a",
              border: "none", borderRadius: 14, padding: "18px",
              fontSize: 16, fontWeight: 700,
              color: canAnalyze ? C.goldText : C.textMuted,
              cursor: canAnalyze ? "pointer" : "not-allowed", transition: ".2s",
            }}
          >
            {analyzing ? "분석 중..." : "분석 시작하기"}
          </button>

          {error && (
            <div style={{ background: "rgba(255,100,100,0.1)", border: "1px solid rgba(255,100,100,0.3)", borderRadius: 12, padding: "14px 16px", fontSize: 13, color: "#ff6b6b" }}>
              {error}
            </div>
          )}
        </>
      )}

      {result && (
        <>
          <div style={{ background: C.surface, borderRadius: 16, padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: 15, fontWeight: 600, color: C.textPrimary }}>분석 완료</div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 32, fontWeight: 700, color: scoreColor(result.score) }}>{result.score.toFixed(1)}점</div>
                <div style={{ fontSize: 13, color: C.textMuted }}>등급: {result.grade}</div>
              </div>
            </div>
            <ScoreBar C={C} label={`정확한 음표: ${result.scoreDetail.correct} / ${result.scoreDetail.total}개`} value={result.score} color={C.gold} />
            <ScoreBar C={C} label={`놓친 음표: ${result.scoreDetail.missedCount}개`} value={Math.max(0, 100 - result.scoreDetail.missedCount * 5)} color="#7ee8a2" />
            <ScoreBar C={C} label={`박자 오류: ${result.scoreDetail.wrongTimingCount}개`} value={Math.max(0, 100 - result.scoreDetail.wrongTimingCount * 10)} color="#80d0ff" />
            <div style={{ fontSize: 12, color: C.textMuted }}>평균 타이밍 편차: {result.scoreDetail.avgTimingDeviation.toFixed(3)}초</div>
          </div>

          {result.feedback && <FeedbackCard C={C} feedback={result.feedback} />}

          <div style={{ display: "flex", gap: 10 }}>
            <button
              onClick={handleReset}
              style={{ flex: 1, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: "14px", fontSize: 14, fontWeight: 600, color: C.textSecondary, cursor: "pointer" }}
            >
              다시 분석
            </button>
            <button
              onClick={() => onNavigate("history")}
              style={{ flex: 1, background: `linear-gradient(135deg,${C.gold},${C.goldDark})`, border: "none", borderRadius: 14, padding: "14px", fontSize: 14, fontWeight: 600, color: C.goldText, cursor: "pointer" }}
            >
              기록 보기 →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
