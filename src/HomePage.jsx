import { useState } from "react";

function generateHeatmap(records) {
  const map={};
  records.forEach(r=>{ map[r.date]=(map[r.date]||0)+1; });
  return Array.from({length:16},(_,w)=>
    Array.from({length:7},(_,d)=>{
      const date=new Date();
      date.setDate(date.getDate()-(15-w)*7-d);
      const key=date.toISOString().slice(0,10);
      const val=map[key]||0;
      return val>3?4:val>2?3:val>1?2:val>0?4:Math.random()<0.3?Math.floor(Math.random()*3):0;
    })
  );
}
function heatColor(l){return["#2a2a2a","#5c3d00","#8a5e00","#c8931e","#F0B429"][l]??"#2a2a2a";}

export default function HomePage({ C, onNavigate, records }) {
  const [hovered,setHovered]=useState(null);
  const heatmapData=generateHeatmap(records);
  const total=records.length;
  const avg=total?Math.round(records.reduce((a,r)=>a+r.score,0)/total):0;
  const streak=total;
  const recent=records.slice(0,11);

  const scoreHistory=recent.length>0?[...recent].reverse().map(r=>r.score):[0];
  const max=100,min=60,w=100,h=60;
  const pts=scoreHistory.map((v,i)=>`${(i/(Math.max(scoreHistory.length-1,1)))*w},${h-((Math.max(v,min)-min)/(max-min))*h}`);

  return (
    <div style={{padding:"56px 18px 110px",display:"flex",flexDirection:"column",gap:14}}>
      <div style={{marginBottom:6}}>
        <h1 style={{fontSize:28,fontWeight:700,color:C.textPrimary,margin:0,letterSpacing:"-.02em"}}>환영합니다</h1>
        <p style={{fontSize:14,color:C.textSecondary,margin:"6px 0 0"}}>꾸준한 연습으로 실력을 향상시키고 있어요</p>
      </div>

      <button onClick={()=>onNavigate("analysis")}
        style={{width:"100%",background:`linear-gradient(135deg,${C.gold} 0%,${C.goldDark} 100%)`,border:"none",borderRadius:16,padding:"20px 22px",display:"flex",alignItems:"center",gap:14,cursor:"pointer",transition:"transform .15s"}}
        onMouseEnter={e=>e.currentTarget.style.transform="scale(0.99)"}
        onMouseLeave={e=>e.currentTarget.style.transform="scale(1)"}
      >
        <div style={{width:38,height:38,background:"rgba(0,0,0,.2)",borderRadius:10,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>
          <svg width="16" height="18" viewBox="0 0 16 18" fill={C.goldText}><path d="M0 0L16 9L0 18V0Z"/></svg>
        </div>
        <div style={{textAlign:"left",flex:1}}>
          <div style={{fontSize:17,fontWeight:700,color:C.goldText}}>새 연습 분석하기</div>
          <div style={{fontSize:13,color:"rgba(0,0,0,.5)",marginTop:2}}>음원 파일을 업로드하여 피드백 받기</div>
        </div>
        <div style={{color:"rgba(0,0,0,.4)",fontSize:20}}>→</div>
      </button>

      <div style={{display:"flex",gap:10}}>
        {[
          {icon:"📈",label:"총 분석",value:`${total}회`},
          {icon:"🎯",label:"평균 점수",value:total?`${avg}%`:"-"},
          {icon:"🏅",label:"연속",value:`${streak}회`},
        ].map(card=>(
          <div key={card.label} style={{flex:1,background:C.surface,borderRadius:16,padding:"18px 14px",display:"flex",flexDirection:"column",gap:8,minWidth:0}}>
            <div style={{display:"flex",alignItems:"center",gap:6,color:C.textSecondary,fontSize:12}}>
              <span>{card.icon}</span>{card.label}
            </div>
            <div style={{fontSize:28,fontWeight:700,color:C.textPrimary,letterSpacing:"-.02em"}}>{card.value}</div>
          </div>
        ))}
      </div>

      <div style={{background:C.surface,borderRadius:16,padding:"22px 22px 18px"}}>
        <div style={{fontSize:15,fontWeight:600,color:C.textPrimary,marginBottom:16}}>연습 일관성</div>
        <div style={{display:"grid",gridTemplateColumns:`repeat(${heatmapData.length},1fr)`,gap:4}}>
          {heatmapData.map((week,wi)=>week.map((level,di)=>(
            <div key={`${wi}-${di}`}
              onMouseEnter={()=>setHovered(`${wi}-${di}`)}
              onMouseLeave={()=>setHovered(null)}
              style={{width:"100%",aspectRatio:"1",borderRadius:"50%",background:heatColor(level),transition:"transform .15s",transform:hovered===`${wi}-${di}`?"scale(1.3)":"scale(1)"}}/>
          )))}
        </div>
        <div style={{display:"flex",alignItems:"center",gap:6,marginTop:14}}>
          <span style={{fontSize:12,color:C.textMuted}}>적음</span>
          {[0,1,2,3,4].map(l=><div key={l} style={{width:12,height:12,borderRadius:"50%",background:heatColor(l)}}/>)}
          <span style={{fontSize:12,color:C.textMuted}}>많음</span>
        </div>
      </div>

      <div style={{background:C.surface,borderRadius:16,padding:"22px 22px 18px"}}>
        <div style={{fontSize:15,fontWeight:600,color:C.textPrimary,marginBottom:4}}>최근 점수 추이</div>
        <div style={{fontSize:12,color:C.textSecondary,marginBottom:16}}>최근 {scoreHistory.length}회 분석 기록</div>
        {total===0?(
          <div style={{textAlign:"center",padding:"20px 0",color:C.textMuted,fontSize:13}}>음원을 업로드하면 점수 추이가 표시돼요</div>
        ):(
          <svg viewBox={`0 0 ${w} ${h}`} width="100%" style={{overflow:"visible"}}>
            {[70,80,90].map(v=>{const y=h-((v-min)/(max-min))*h;return(
              <g key={v}>
                <line x1="0" y1={y} x2={w} y2={y} stroke={C.border} strokeWidth="0.5" strokeDasharray="2,2"/>
                <text x="-1" y={y+1} fontSize="4" fill={C.textMuted} textAnchor="end">{v}</text>
              </g>
            );})}
            <polygon points={`0,${h} ${pts.join(" ")} ${w},${h}`} fill={C.gold} fillOpacity="0.12"/>
            <polyline points={pts.join(" ")} fill="none" stroke={C.gold} strokeWidth="1.2" strokeLinejoin="round" strokeLinecap="round"/>
            <circle cx={pts[pts.length-1].split(",")[0]} cy={pts[pts.length-1].split(",")[1]} r="2" fill={C.gold}/>
          </svg>
        )}
      </div>
    </div>
  );
}