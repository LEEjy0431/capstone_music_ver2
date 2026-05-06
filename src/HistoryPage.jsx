import { useState } from "react";

function scoreColor(s,C){ return s>=90?"#80d0ff":s>=80?C.gold:"#ff9f43"; }

export default function HistoryPage({ C, records }) {
  const [search,setSearch]=useState("");
  const filtered=records.filter(r=>r.title.includes(search));
  const total=filtered.length;
  const avg=total?Math.round(filtered.reduce((a,r)=>a+r.score,0)/total):0;
  const aCount=filtered.filter(r=>r.grade.startsWith("A")).length;

  return (
    <div style={{padding:"56px 18px 110px",display:"flex",flexDirection:"column",gap:16}}>
      <div>
        <h1 style={{fontSize:28,fontWeight:700,color:C.textPrimary,margin:0,letterSpacing:"-.02em"}}>연습 기록</h1>
        <p style={{fontSize:14,color:C.textSecondary,margin:"6px 0 0"}}>지난 연습 세션을 모두 확인하세요</p>
      </div>

      <div style={{display:"flex",alignItems:"center",gap:10,background:C.surface,borderRadius:12,padding:"12px 16px"}}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={C.textMuted} strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="곡 제목으로 검색..."
          style={{background:"none",border:"none",outline:"none",color:C.textPrimary,fontSize:14,width:"100%"}}/>
      </div>

      {filtered.length===0?(
        <div style={{background:C.surface,borderRadius:16,padding:"48px 24px",textAlign:"center"}}>
          <div style={{fontSize:40,marginBottom:12}}>🎵</div>
          <div style={{fontSize:16,fontWeight:600,color:C.textPrimary,marginBottom:6}}>아직 기록이 없어요</div>
          <div style={{fontSize:13,color:C.textSecondary}}>분석 탭에서 음원을 업로드해보세요</div>
        </div>
      ):(
        <div style={{background:C.surface,borderRadius:16,overflow:"hidden"}}>
          {filtered.map((r,i)=>(
            <div key={r.id}
              style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"18px 20px",borderBottom:i<filtered.length-1?`1px solid ${C.border}`:"none",cursor:"pointer",transition:"background .15s"}}
              onMouseEnter={e=>e.currentTarget.style.background=C.surfaceHover}
              onMouseLeave={e=>e.currentTarget.style.background="transparent"}
            >
              <div style={{flex:1,minWidth:0}}>
                <div style={{fontSize:15,fontWeight:600,color:C.textPrimary,marginBottom:4,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{r.title}</div>
                <div style={{fontSize:12,color:C.textSecondary,display:"flex",gap:6,alignItems:"center"}}>
                  {r.date}<span style={{color:C.border}}>•</span>{r.time}<span style={{color:C.border}}>•</span>{r.duration}
                </div>
              </div>
              <div style={{display:"flex",alignItems:"center",gap:12,flexShrink:0,marginLeft:12}}>
                <div style={{textAlign:"right"}}>
                  <div style={{fontSize:18,fontWeight:700,color:scoreColor(r.score,C)}}>{r.score}%</div>
                  <div style={{fontSize:12,color:C.textMuted}}>{r.grade}</div>
                </div>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={C.textMuted} strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </div>
            </div>
          ))}
        </div>
      )}

      {total>0&&(
        <div style={{background:C.surface,borderRadius:16,padding:"20px",display:"flex",justifyContent:"space-around"}}>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:28,fontWeight:700,color:C.gold}}>{total}회</div>
            <div style={{fontSize:12,color:C.textSecondary,marginTop:4}}>총 세션</div>
          </div>
          <div style={{width:1,background:C.border}}/>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:28,fontWeight:700,color:"#80d0ff"}}>{avg}%</div>
            <div style={{fontSize:12,color:C.textSecondary,marginTop:4}}>평균 점수</div>
          </div>
          <div style={{width:1,background:C.border}}/>
          <div style={{textAlign:"center"}}>
            <div style={{fontSize:28,fontWeight:700,color:"#c77dff"}}>{aCount}회</div>
            <div style={{fontSize:12,color:C.textSecondary,marginTop:4}}>A 등급</div>
          </div>
        </div>
      )}
    </div>
  );
}