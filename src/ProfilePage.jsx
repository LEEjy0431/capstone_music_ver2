import { useState } from "react";

function Toggle({ on, setOn, C }) {
  return (
    <div onClick={()=>setOn(!on)} style={{width:48,height:26,borderRadius:13,background:on?"#00c8ff":C.border,position:"relative",cursor:"pointer",transition:"background .2s"}}>
      <div style={{position:"absolute",top:3,left:on?25:3,width:20,height:20,borderRadius:"50%",background:"#fff",transition:"left .2s",boxShadow:"0 1px 3px rgba(0,0,0,.3)"}}/>
    </div>
  );
}

function getAchievements(records) {
  const total=records.length;
  const best=total?Math.max(...records.map(r=>r.score)):0;
  const lateNight=records.some(r=>r.time.includes("오후")&&parseInt(r.time.split(" ")[1])>=10);
  const earlyMorning=records.some(r=>r.time.includes("오전")&&parseInt(r.time.split(" ")[1])<7);
  return [
    {icon:"🔥",name:"주간 워리어",  desc:"7회 이상 분석 완료",  done:total>=7},
    {icon:"⭐",name:"완벽주의자",  desc:"95% 이상 점수 달성",  done:best>=95},
    {icon:"💯",name:"백전노장",    desc:"10회 이상 분석 완료", done:total>=10},
    {icon:"🦉",name:"올빼미",      desc:"밤 10시 이후 업로드", done:lateNight},
    {icon:"🌅",name:"아침형 인간", desc:"오전 7시 이전 업로드", done:earlyMorning},
    {icon:"🎓",name:"마스터",      desc:"50회 이상 분석 완료", done:total>=50},
  ];
}

export default function ProfilePage({ C, darkMode, setDarkMode, profile, setProfile, records }) {
  const [editing,setEditing]=useState(false);
  const [form,setForm]=useState({...profile});
  const [emailAlert,setEmailAlert]=useState(true);
  const [autoRecord,setAutoRecord]=useState(true);

  const achievements=getAchievements(records);
  const total=records.length;
  const avg=total?Math.round(records.reduce((a,r)=>a+r.score,0)/total):0;

  function saveProfile(){ setProfile(form); setEditing(false); }

  return (
    <div style={{padding:"56px 18px 110px",display:"flex",flexDirection:"column",gap:14}}>
      <div>
        <h1 style={{fontSize:28,fontWeight:700,color:C.textPrimary,margin:0,letterSpacing:"-.02em"}}>프로필</h1>
        <p style={{fontSize:14,color:C.textSecondary,margin:"6px 0 0"}}>계정 및 설정 관리</p>
      </div>

      {/* 프로필 카드 */}
      <div style={{background:C.surface,borderRadius:16,padding:20}}>
        <div style={{display:"flex",alignItems:"center",gap:16,marginBottom:16}}>
          <div style={{width:64,height:64,borderRadius:"50%",background:"linear-gradient(135deg,#c77dff,#80d0ff)",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div style={{flex:1}}>
            {editing?(
              <input value={form.name} onChange={e=>setForm({...form,name:e.target.value})}
                style={{background:C.cardBg,border:`1px solid ${C.border}`,borderRadius:8,padding:"6px 10px",color:C.textPrimary,fontSize:18,fontWeight:700,width:"100%",marginBottom:6}}/>
            ):(
              <div style={{fontSize:20,fontWeight:700,color:C.textPrimary}}>{profile.name}</div>
            )}
            {editing?(
              <input value={form.email} onChange={e=>setForm({...form,email:e.target.value})}
                style={{background:C.cardBg,border:`1px solid ${C.border}`,borderRadius:8,padding:"6px 10px",color:C.textSecondary,fontSize:13,width:"100%"}}/>
            ):(
              <div style={{fontSize:13,color:C.textSecondary,marginTop:2}}>{profile.email}</div>
            )}
          </div>
          {editing?(
            <button onClick={saveProfile} style={{background:C.gold,border:"none",borderRadius:10,padding:"8px 14px",color:C.goldText,fontSize:13,fontWeight:700,cursor:"pointer"}}>저장</button>
          ):(
            <button onClick={()=>{setForm({...profile});setEditing(true);}} style={{background:"none",border:`1px solid ${C.border}`,borderRadius:10,padding:"8px 14px",color:C.textSecondary,fontSize:13,cursor:"pointer"}}>⚙️ 수정</button>
          )}
        </div>
        <div style={{display:"flex",gap:10}}>
          {[
            {label:"가입일",  value:profile.joinDate,highlight:false},
            {label:"실력 수준",value:profile.level,   highlight:true},
            {label:"총 분석", value:`${total}회`,     highlight:false},
            {label:"평균 점수",value:`${avg}%`,        highlight:false},
          ].map(item=>(
            <div key={item.label} style={{background:C.cardBg,borderRadius:10,padding:"10px 12px",flex:1,minWidth:0}}>
              <div style={{fontSize:10,color:C.textMuted,marginBottom:4}}>{item.label}</div>
              <div style={{fontSize:13,fontWeight:600,color:item.highlight?C.gold:C.textPrimary,whiteSpace:"nowrap"}}>{item.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 업적 */}
      <div style={{background:C.surface,borderRadius:16,padding:20}}>
        <div style={{fontSize:15,fontWeight:600,color:C.textPrimary,marginBottom:14}}>
          🏅 업적 <span style={{fontSize:12,color:C.textMuted,fontWeight:400}}>({achievements.filter(a=>a.done).length}/{achievements.length})</span>
        </div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
          {achievements.map(a=>(
            <div key={a.name} style={{background:C.cardBg,borderRadius:12,padding:"14px",display:"flex",alignItems:"flex-start",gap:10,opacity:a.done?1:0.45}}>
              <span style={{fontSize:22}}>{a.icon}</span>
              <div style={{flex:1,minWidth:0}}>
                <div style={{fontSize:13,fontWeight:600,color:C.textPrimary,marginBottom:3}}>{a.name}</div>
                <div style={{fontSize:11,color:C.textSecondary,lineHeight:1.4}}>{a.desc}</div>
              </div>
              {a.done&&(
                <div style={{width:18,height:18,borderRadius:"50%",background:C.gold,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,fontSize:10,color:C.goldText,fontWeight:700}}>✓</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 환경 설정 */}
      <div style={{background:C.surface,borderRadius:16,padding:20}}>
        <div style={{fontSize:15,fontWeight:600,color:C.textPrimary,marginBottom:14}}>환경 설정</div>
        {[
          {label:"이메일 알림",  icon:"🔔",state:emailAlert,set:setEmailAlert},
          {label:"다크 모드",    icon:"🌙",state:darkMode,  set:setDarkMode},
          {label:"세션 자동 기록",icon:"🎵",state:autoRecord,set:setAutoRecord},
        ].map((item,i,arr)=>(
          <div key={item.label} style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"14px 16px",background:C.cardBg,borderRadius:12,marginBottom:i<arr.length-1?8:0}}>
            <div style={{display:"flex",alignItems:"center",gap:10,fontSize:14,color:C.textPrimary}}>
              <span>{item.icon}</span>{item.label}
            </div>
            <Toggle on={item.state} setOn={item.set} C={C}/>
          </div>
        ))}
      </div>

      {/* 실력 수준 */}
      <div style={{background:C.surface,borderRadius:16,padding:20}}>
        <div style={{fontSize:15,fontWeight:600,color:C.textPrimary,marginBottom:14}}>실력 수준</div>
        <div style={{display:"flex",gap:8}}>
          {["입문","초급","중급","고급","전문가"].map(level=>(
            <button key={level} onClick={()=>setProfile({...profile,level})}
              style={{flex:1,padding:"10px 4px",borderRadius:10,border:`1px solid ${profile.level===level?C.gold:C.border}`,background:profile.level===level?"rgba(240,180,41,0.15)":C.cardBg,color:profile.level===level?C.gold:C.textSecondary,fontSize:12,fontWeight:profile.level===level?700:400,cursor:"pointer",transition:".2s"}}>
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* 로그아웃 */}
      <button style={{width:"100%",background:C.surface,border:"none",borderRadius:16,padding:18,fontSize:15,fontWeight:600,color:"#ff6b6b",cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",gap:8}}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
        로그아웃
      </button>
    </div>
  );
}