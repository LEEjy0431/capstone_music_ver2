export default function StatsPage({ C, records }) {
  const total=records.length;
  const avg=total?Math.round(records.reduce((a,r)=>a+r.score,0)/total):0;
  const best=total?records.reduce((a,r)=>r.score>a.score?r:a,records[0]):null;
  const avgPitch=total?Math.round(records.reduce((a,r)=>a+r.pitch,0)/total):0;
  const avgRhythm=total?Math.round(records.reduce((a,r)=>a+r.rhythm,0)/total):0;
  const avgDynamics=total?Math.round(records.reduce((a,r)=>a+r.dynamics,0)/total):0;
  const avgTempo=total?Math.round(records.reduce((a,r)=>a+r.tempo,0)/total):0;

  const days=["일","월","화","수","목","금","토"];
  const dayCounts=Array(7).fill(0);
  records.forEach(r=>{ const d=new Date(r.date).getDay(); dayCounts[d]++; });
  const weekData=days.map((day,i)=>({day,val:dayCounts[i]}));
  const maxVal=Math.max(...weekData.map(d=>d.val),1);

  const radarSkills=[
    {label:"리듬",value:avgRhythm},
    {label:"음정",value:avgPitch},
    {label:"다이나믹",value:avgDynamics},
    {label:"템포",value:avgTempo},
    {label:"종합",value:avg},
  ];
  const cx=150,cy=150,r=100,n=radarSkills.length;
  const gridPoints=(ratio)=>radarSkills.map((_,i)=>{
    const angle=(Math.PI*2*i)/n-Math.PI/2;
    return `${cx+r*ratio*Math.cos(angle)},${cy+r*ratio*Math.sin(angle)}`;
  }).join(" ");
  const dataPoints=radarSkills.map((s,i)=>{
    const angle=(Math.PI*2*i)/n-Math.PI/2;
    return {x:cx+r*(s.value/100)*Math.cos(angle),y:cy+r*(s.value/100)*Math.sin(angle)};
  });
  const labelPoints=radarSkills.map((s,i)=>{
    const angle=(Math.PI*2*i)/n-Math.PI/2;
    return {x:cx+(r+22)*Math.cos(angle),y:cy+(r+22)*Math.sin(angle),label:s.label};
  });

  if(total===0) return (
    <div style={{padding:"56px 18px 110px",display:"flex",flexDirection:"column",gap:16}}>
      <div>
        <h1 style={{fontSize:28,fontWeight:700,color:C.textPrimary,margin:0,letterSpacing:"-.02em"}}>통계</h1>
        <p style={{fontSize:14,color:C.textSecondary,margin:"6px 0 0"}}>연습 여정에 대한 상세 인사이트</p>
      </div>
      <div style={{background:C.surface,borderRadius:16,padding:"48px 24px",textAlign:"center",marginTop:20}}>
        <div style={{fontSize:40,marginBottom:12}}>📊</div>
        <div style={{fontSize:16,fontWeight:600,color:C.textPrimary,marginBottom:6}}>아직 데이터가 없어요</div>
        <div style={{fontSize:13,color:C.textSecondary}}>음원을 업로드하면 통계가 자동으로 생성돼요</div>
      </div>
    </div>
  );

  return (
    <div style={{padding:"56px 18px 110px",display:"flex",flexDirection:"column",gap:14}}>
      <div>
        <h1 style={{fontSize:28,fontWeight:700,color:C.textPrimary,margin:0,letterSpacing:"-.02em"}}>통계</h1>
        <p style={{fontSize:14,color:C.textSecondary,margin:"6px 0 0"}}>연습 여정에 대한 상세 인사이트</p>
      </div>

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
        {[
          {icon:"🎵",label:"총 세션",value:`${total}회`,sub:"전체",color:C.textPrimary},
          {icon:"📈",label:"평균 점수",value:`${avg}%`,sub:"전체 평균",color:C.gold},
          {icon:"🎯",label:"최고 점수",value:best?`${best.score}%`:"-",sub:best?best.title.slice(0,8)+"...":"-",color:C.textPrimary},
          {icon:"🏅",label:"A등급",value:`${records.filter(r=>r.grade.startsWith("A")).length}회`,sub:"전체 중",color:"#80d0ff"},
        ].map(card=>(
          <div key={card.label} style={{background:C.surface,borderRadius:14,padding:"16px 18px"}}>
            <div style={{fontSize:12,color:C.textSecondary,marginBottom:8}}>{card.icon} {card.label}</div>
            <div style={{fontSize:26,fontWeight:700,color:card.color,letterSpacing:"-.02em"}}>{card.value}</div>
            <div style={{fontSize:11,color:C.textMuted,marginTop:4}}>{card.sub}</div>
          </div>
        ))}
      </div>

      <div style={{background:C.surface,borderRadius:16,padding:"22px 22px 18px"}}>
        <div style={{fontSize:15,fontWeight:600,color:C.textPrimary,marginBottom:20}}>요일별 활동</div>
        <div style={{display:"flex",alignItems:"flex-end",gap:8,height:120}}>
          {weekData.map(d=>(
            <div key={d.day} style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",gap:6}}>
              <div style={{width:"100%",height:`${Math.max((d.val/maxVal)*90,4)}px`,background:d.val>0?"#80d0ff":C.border,borderRadius:"6px 6px 0 0",transition:"height .3s"}}/>
              <span style={{fontSize:11,color:C.textSecondary}}>{d.day}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{background:C.surface,borderRadius:16,padding:"22px 22px 18px"}}>
        <div style={{fontSize:15,fontWeight:600,color:C.textPrimary,marginBottom:16}}>스킬 평가</div>
        <svg viewBox="0 0 300 300" width="100%">
          {[25,50,75,100].map(l=><polygon key={l} points={gridPoints(l/100)} fill="none" stroke={C.border} strokeWidth="0.8"/>)}
          {radarSkills.map((_,i)=>{
            const angle=(Math.PI*2*i)/n-Math.PI/2;
            return <line key={i} x1={cx} y1={cy} x2={cx+r*Math.cos(angle)} y2={cy+r*Math.sin(angle)} stroke={C.border} strokeWidth="0.8"/>;
          })}
          {[25,50,75,100].map(l=><text key={l} x={cx+3} y={cy-r*l/100+4} fontSize="8" fill={C.textMuted}>{l}</text>)}
          <polygon points={dataPoints.map(p=>`${p.x},${p.y}`).join(" ")} fill={C.gold} fillOpacity="0.25" stroke={C.gold} strokeWidth="1.5"/>
          {dataPoints.map((p,i)=><circle key={i} cx={p.x} cy={p.y} r="3" fill={C.gold}/>)}
          {labelPoints.map((p,i)=><text key={i} x={p.x} y={p.y} fontSize="11" fill={C.textSecondary} textAnchor="middle" dominantBaseline="middle">{p.label}</text>)}
        </svg>
      </div>

      <div style={{background:C.surface,borderRadius:16,padding:"22px 22px 18px"}}>
        <div style={{fontSize:15,fontWeight:600,color:C.textPrimary,marginBottom:16}}>항목별 평균</div>
        {[
          {label:"음정 정확도",value:avgPitch,  color:C.gold},
          {label:"리듬 안정성",value:avgRhythm, color:"#7ee8a2"},
          {label:"다이나믹",   value:avgDynamics,color:"#80d0ff"},
          {label:"템포 일관성",value:avgTempo,  color:"#c77dff"},
        ].map(item=>(
          <div key={item.label} style={{marginBottom:14}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}>
              <span style={{fontSize:13,color:C.textSecondary}}>{item.label}</span>
              <span style={{fontSize:13,fontWeight:700,color:item.color}}>{item.value}%</span>
            </div>
            <div style={{height:6,background:"#2a2a2a",borderRadius:3}}>
              <div style={{height:"100%",width:`${item.value}%`,background:item.color,borderRadius:3}}/>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}