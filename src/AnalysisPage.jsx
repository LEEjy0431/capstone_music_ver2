import { useState, useRef } from "react";
import { getApiBase } from "./App";

const LANG_OPTIONS = [
  { code: "ko", label: "한국어" },
  { code: "en", label: "English" },
  { code: "ja", label: "日本語" },
  { code: "zh", label: "中文" },
];

// ── 파일 드롭존 ──────────────────────────────────────────────────────────
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
          <div style={{ background: C.gold, color: C.goldText, borderRadius: 8, padding: "6px 16px", fontSize: 12, fontWeight: 700, marginTop: 4 }}>파일 선택</div>
        </>
      )}
      <input ref={inputRef} type="file" accept={accept} style={{ display: "none" }} onChange={(e) => e.target.files[0] && onFile(e.target.files[0])} />
    </div>
  );
}

// ── 점수 바 ──────────────────────────────────────────────────────────────
function ScoreBar({ C, label, fraction, color }) {
  const pct = Math.max(0, Math.min(100, fraction * 100));
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
        <span style={{ fontSize: 13, color: C.textSecondary }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 700, color }}>{pct.toFixed(0)}%</span>
      </div>
      <div style={{ height: 6, background: "#2a2a2a", borderRadius: 3 }}>
        <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 3, transition: "width 1s ease" }} />
      </div>
    </div>
  );
}

// ── GPT 피드백 카드 ──────────────────────────────────────────────────────
function FeedbackCard({ C, feedback }) {
  return (
    <div style={{ background: C.cardBg, borderRadius: 14, padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ fontSize: 15, fontWeight: 700, color: C.textPrimary }}>AI 피드백</div>
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

// ── 스트리밍 중 표시 카드 ────────────────────────────────────────────────
function StreamingCard({ C, text }) {
  return (
    <div style={{ background: C.cardBg, borderRadius: 14, padding: 18 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <Spinner color={C.gold} size={14} />
        <span style={{ fontSize: 14, fontWeight: 700, color: C.gold }}>AI 피드백 생성 중...</span>
      </div>
      <div style={{ fontSize: 13, color: C.textSecondary, lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{text}</div>
    </div>
  );
}

function Spinner({ color = "#F0B429", size = 16 }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%",
      border: `2px solid ${color}40`,
      borderTopColor: color,
      animation: "spin .7s linear infinite",
    }}>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  );
}

// ── 메인 컴포넌트 ────────────────────────────────────────────────────────
export default function AnalysisPage({ C, onNavigate, onAnalyze, onFeedback }) {
  const [audioFile, setAudioFile] = useState(null);
  const [sheetFile, setSheetFile] = useState(null);
  const [lang, setLang] = useState("ko");

  // 단계 상태
  const [step, setStep] = useState("idle"); // idle | analyzing | streaming | done | error
  const [result, setResult] = useState(null);
  const [streamText, setStreamText] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState(null);

  const busy = step === "analyzing" || step === "streaming";

  async function handleAnalyze() {
    if (!audioFile || !sheetFile || busy) return;

    setStep("analyzing");
    setError(null);
    setResult(null);
    setStreamText("");
    setFeedback(null);

    let record;
    try {
      // Step 1: Python 채점
      record = await onAnalyze(sheetFile, audioFile, lang);
      setResult(record);
    } catch (e) {
      setError(e.message || "분석 중 오류가 발생했습니다.");
      setStep("error");
      return;
    }

    // Step 2: GPT SSE 스트리밍
    if (!record.sessionId) { setStep("done"); return; }
    setStep("streaming");

    const url = `${getApiBase()}/api/feedback/stream?session_id=${encodeURIComponent(record.sessionId)}&lang=${lang}`;
    const buffer = { text: "" };

    try {
      const res = await fetch(url);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let rawChunk = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        rawChunk += decoder.decode(value, { stream: true });
        const blocks = rawChunk.split("\n\n");
        rawChunk = blocks.pop(); // 마지막 불완전 블록 유지

        for (const block of blocks) {
          const eventLine = block.match(/^event: (.+)/m)?.[1]?.trim();
          const dataLine = block.match(/^data: (.+)/m)?.[1]?.trim();
          if (!dataLine) continue;

          const payload = JSON.parse(dataLine);

          if (eventLine === "chunk" && payload.text) {
            buffer.text += payload.text;
            setStreamText(buffer.text);
          } else if (eventLine === "done" && payload.feedback) {
            onFeedback(record.id, payload.feedback);
            setFeedback(payload.feedback);
            setStep("done");
          } else if (eventLine === "error") {
            setError(payload.error || "피드백 생성 실패");
            setStep("done"); // 점수는 이미 있으므로 done 처리
          }
        }
      }
    } catch (e) {
      // SSE 오류는 치명적이지 않음 — 점수 카드는 유지
      setError("AI 피드백 연결 실패. 점수는 저장되었습니다.");
      setStep("done");
    }
  }

  function handleReset() {
    setAudioFile(null);
    setSheetFile(null);
    setResult(null);
    setStreamText("");
    setFeedback(null);
    setError(null);
    setStep("idle");
  }

  const scoreColor = (v) => v >= 90 ? "#80d0ff" : v >= 80 ? C.gold : "#ff9f43";

  return (
    <div style={{ padding: "56px 18px 110px", display: "flex", flexDirection: "column", gap: 16 }}>
      <div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: C.textPrimary, margin: 0 }}>연습 분석</h1>
        <p style={{ fontSize: 14, color: C.textSecondary, margin: "6px 0 0" }}>악보와 음원을 업로드해 AI 피드백을 받으세요</p>
      </div>

      {/* 파일 선택 (결과 없을 때만) */}
      {step === "idle" && (
        <>
          <FileDropZone C={C} label="연주 음원 (WAV)" accept=".wav,audio/*" hint="WAV 파일을 드래그하거나 클릭" file={audioFile} onFile={setAudioFile} />
          <FileDropZone C={C} label="악보 파일 (MusicXML)" accept=".xml,.mxl" hint="MusicXML 파일을 드래그하거나 클릭" file={sheetFile} onFile={setSheetFile} />

          {/* 언어 선택 */}
          <div style={{ background: C.surface, borderRadius: 14, padding: "14px 16px" }}>
            <div style={{ fontSize: 13, color: C.textSecondary, marginBottom: 10, fontWeight: 600 }}>피드백 언어</div>
            <div style={{ display: "flex", gap: 8 }}>
              {LANG_OPTIONS.map((l) => (
                <button key={l.code} onClick={() => setLang(l.code)} style={{ flex: 1, padding: "8px 0", borderRadius: 20, border: "none", fontSize: 12, fontWeight: 600, cursor: "pointer", transition: ".2s", background: lang === l.code ? C.gold : C.cardBg, color: lang === l.code ? C.goldText : C.textSecondary }}>
                  {l.label}
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      {/* 분석 버튼 */}
      {(step === "idle" || step === "error") && (
        <button
          onClick={handleAnalyze}
          disabled={!audioFile || !sheetFile}
          style={{ width: "100%", background: (audioFile && sheetFile) ? `linear-gradient(135deg,${C.gold},${C.goldDark})` : "#2a2a2a", border: "none", borderRadius: 14, padding: "18px", fontSize: 16, fontWeight: 700, color: (audioFile && sheetFile) ? C.goldText : C.textMuted, cursor: (audioFile && sheetFile) ? "pointer" : "not-allowed" }}
        >
          분석 시작하기
        </button>
      )}

      {/* Step 1 진행 중 */}
      {step === "analyzing" && (
        <div style={{ background: C.surface, borderRadius: 14, padding: 20, display: "flex", alignItems: "center", gap: 12 }}>
          <Spinner color={C.gold} size={20} />
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: C.textPrimary }}>연주 채점 중...</div>
            <div style={{ fontSize: 12, color: C.textMuted, marginTop: 4 }}>피아노 음표 분석 중 (10~30초 소요)</div>
          </div>
        </div>
      )}

      {/* 점수 카드 (Step 1 완료 후) */}
      {result && (
        <div style={{ background: C.surface, borderRadius: 16, padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div style={{ fontSize: 13, color: C.textMuted, marginBottom: 4 }}>{result.title}</div>
              <div style={{ fontSize: 13, color: C.textMuted }}>{result.date} {result.time}</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 36, fontWeight: 700, color: scoreColor(result.score), lineHeight: 1 }}>{result.score.toFixed(1)}</div>
              <div style={{ fontSize: 12, color: C.textMuted }}>점</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: scoreColor(result.score), marginTop: 2 }}>{result.grade}</div>
            </div>
          </div>
          <ScoreBar C={C} label={`음정 정확도 (${result.scoreDetail.correct}/${result.scoreDetail.total})`} fraction={result.scoreDetail.total > 0 ? result.scoreDetail.correct / result.scoreDetail.total : 0} color={C.gold} />
          <ScoreBar C={C} label={`누락 음표 ${result.scoreDetail.missedCount}개`} fraction={result.scoreDetail.total > 0 ? 1 - result.scoreDetail.missedCount / result.scoreDetail.total : 1} color="#7ee8a2" />
          <ScoreBar C={C} label={`박자 오류 ${result.scoreDetail.wrongTimingCount}개`} fraction={result.scoreDetail.total > 0 ? 1 - result.scoreDetail.wrongTimingCount / result.scoreDetail.total : 1} color="#80d0ff" />
          <div style={{ fontSize: 12, color: C.textMuted }}>평균 타이밍 편차: {result.scoreDetail.avgTimingDeviation.toFixed(3)}초</div>
        </div>
      )}

      {/* Step 2 스트리밍 중 */}
      {step === "streaming" && streamText && <StreamingCard C={C} text={streamText} />}

      {/* Step 2 완료 */}
      {feedback && <FeedbackCard C={C} feedback={feedback} />}

      {/* 오류 메시지 */}
      {error && (
        <div style={{ background: "rgba(255,100,100,0.1)", border: "1px solid rgba(255,100,100,0.3)", borderRadius: 12, padding: "14px 16px", fontSize: 13, color: "#ff6b6b" }}>
          {error}
        </div>
      )}

      {/* 완료 후 버튼 */}
      {(step === "done" || (step === "error" && result)) && (
        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={handleReset} style={{ flex: 1, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 14, fontSize: 14, fontWeight: 600, color: C.textSecondary, cursor: "pointer" }}>
            다시 분석
          </button>
          <button onClick={() => onNavigate("history")} style={{ flex: 1, background: `linear-gradient(135deg,${C.gold},${C.goldDark})`, border: "none", borderRadius: 14, padding: 14, fontSize: 14, fontWeight: 600, color: C.goldText, cursor: "pointer" }}>
            기록 보기 →
          </button>
        </div>
      )}
    </div>
  );
}
