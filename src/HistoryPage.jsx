import { useState } from "react";

function scoreColor(s, C) { return s >= 90 ? "#80d0ff" : s >= 80 ? C.gold : "#ff9f43"; }

function FeedbackSection({ C, feedback }) {
  return (
    <div style={{ padding: "0 20px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
      {[
        { label: "종합 평가", text: feedback.overall, color: C.gold },
        { label: "음정", text: feedback.pitch, color: "#80d0ff" },
        { label: "리듬", text: feedback.rhythm, color: "#7ee8a2" },
        { label: "타이밍", text: feedback.timing, color: "#c77dff" },
      ].map(item => (
        <div key={item.label}>
          <div style={{ fontSize: 11, fontWeight: 700, color: item.color, marginBottom: 3 }}>{item.label}</div>
          <div style={{ fontSize: 12, color: C.textSecondary, lineHeight: 1.6 }}>{item.text}</div>
        </div>
      ))}
      {feedback.tips?.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#ff9f43", marginBottom: 5 }}>개선 포인트</div>
          {feedback.tips.map((tip, i) => (
            <div key={i} style={{ display: "flex", gap: 6, marginBottom: 4 }}>
              <span style={{ color: "#ff9f43", fontSize: 12, flexShrink: 0 }}>{i + 1}.</span>
              <span style={{ fontSize: 12, color: C.textSecondary, lineHeight: 1.5 }}>{tip}</span>
            </div>
          ))}
        </div>
      )}
      {feedback.encouragement && (
        <div style={{ background: "rgba(240,180,41,0.08)", borderRadius: 8, padding: "10px 12px", fontSize: 12, color: C.gold, fontStyle: "italic", lineHeight: 1.6 }}>
          {feedback.encouragement}
        </div>
      )}
    </div>
  );
}

function RecordItem({ C, r, onDelete }) {
  const [open, setOpen] = useState(false);
  const [confirm, setConfirm] = useState(false);

  return (
    <div style={{ borderBottom: `1px solid ${C.border}` }}>
      {/* 헤더 행 */}
      <div
        style={{ display: "flex", alignItems: "center", padding: "16px 20px", cursor: "pointer", transition: "background .15s" }}
        onClick={() => setOpen(o => !o)}
        onMouseEnter={e => e.currentTarget.style.background = C.surfaceHover}
        onMouseLeave={e => e.currentTarget.style.background = "transparent"}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: C.textPrimary, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{r.title}</div>
          <div style={{ fontSize: 12, color: C.textSecondary, marginTop: 3 }}>{r.date} {r.time}</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0, marginLeft: 10 }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: scoreColor(r.score, C) }}>{r.score.toFixed(1)}점</div>
            <div style={{ fontSize: 11, color: C.textMuted }}>{r.grade}</div>
          </div>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={C.textMuted} strokeWidth="2" style={{ transform: open ? "rotate(90deg)" : "none", transition: ".2s", flexShrink: 0 }}>
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>
      </div>

      {/* 펼쳐진 영역 */}
      {open && (
        <div>
          {r.feedback
            ? <FeedbackSection C={C} feedback={r.feedback} />
            : <div style={{ padding: "0 20px 16px", fontSize: 13, color: C.textMuted }}>피드백 없음</div>
          }
          {/* 삭제 버튼 */}
          {!confirm
            ? <div style={{ padding: "0 20px 16px" }}>
                <button onClick={() => setConfirm(true)} style={{ background: "rgba(255,80,80,0.1)", border: "1px solid rgba(255,80,80,0.2)", borderRadius: 8, padding: "8px 16px", fontSize: 12, color: "#ff6b6b", cursor: "pointer", fontWeight: 600 }}>
                  기록 삭제
                </button>
              </div>
            : <div style={{ padding: "0 20px 16px", display: "flex", gap: 8 }}>
                <button onClick={() => onDelete(r.id)} style={{ flex: 1, background: "rgba(255,80,80,0.15)", border: "1px solid rgba(255,80,80,0.3)", borderRadius: 8, padding: "10px", fontSize: 13, color: "#ff6b6b", cursor: "pointer", fontWeight: 700 }}>
                  삭제 확인
                </button>
                <button onClick={() => setConfirm(false)} style={{ flex: 1, background: C.cardBg, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px", fontSize: 13, color: C.textSecondary, cursor: "pointer" }}>
                  취소
                </button>
              </div>
          }
        </div>
      )}
    </div>
  );
}

export default function HistoryPage({ C, records, onDelete }) {
  const [search, setSearch] = useState("");
  const filtered = records.filter(r => r.title.toLowerCase().includes(search.toLowerCase()));
  const total = filtered.length;
  const avg = total ? (filtered.reduce((a, r) => a + r.score, 0) / total).toFixed(1) : 0;
  const aCount = filtered.filter(r => r.grade.startsWith("A")).length;

  return (
    <div style={{ padding: "56px 18px 110px", display: "flex", flexDirection: "column", gap: 16 }}>
      <div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: C.textPrimary, margin: 0 }}>연습 기록</h1>
        <p style={{ fontSize: 14, color: C.textSecondary, margin: "6px 0 0" }}>지난 연습 세션을 모두 확인하세요</p>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10, background: C.surface, borderRadius: 12, padding: "12px 16px" }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={C.textMuted} strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="곡 제목으로 검색..."
          style={{ background: "none", border: "none", outline: "none", color: C.textPrimary, fontSize: 14, width: "100%" }} />
      </div>

      {filtered.length === 0 ? (
        <div style={{ background: C.surface, borderRadius: 16, padding: "48px 24px", textAlign: "center" }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🎵</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: C.textPrimary, marginBottom: 6 }}>아직 기록이 없어요</div>
          <div style={{ fontSize: 13, color: C.textSecondary }}>분석 탭에서 음원을 업로드해보세요</div>
        </div>
      ) : (
        <div style={{ background: C.surface, borderRadius: 16, overflow: "hidden" }}>
          {filtered.map(r => (
            <RecordItem key={r.id} C={C} r={r} onDelete={onDelete} />
          ))}
        </div>
      )}

      {total > 0 && (
        <div style={{ background: C.surface, borderRadius: 16, padding: 20, display: "flex", justifyContent: "space-around" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: C.gold }}>{total}회</div>
            <div style={{ fontSize: 12, color: C.textSecondary, marginTop: 4 }}>총 세션</div>
          </div>
          <div style={{ width: 1, background: C.border }} />
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#80d0ff" }}>{avg}점</div>
            <div style={{ fontSize: 12, color: C.textSecondary, marginTop: 4 }}>평균 점수</div>
          </div>
          <div style={{ width: 1, background: C.border }} />
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#c77dff" }}>{aCount}회</div>
            <div style={{ fontSize: 12, color: C.textSecondary, marginTop: 4 }}>A 등급</div>
          </div>
        </div>
      )}
    </div>
  );
}
